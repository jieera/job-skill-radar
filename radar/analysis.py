import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.skip += 1
        if tag in {"p", "li", "br", "div", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.skip = max(0, self.skip - 1)
        if tag in {"p", "li", "div", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def plain(html):
    parser = TextParser()
    parser.feed(html or "")
    return "\n".join(re.sub(r"[ \t\xa0]+", " ", line).strip()
                     for line in "".join(parser.parts).splitlines() if line.strip())


def pattern(alias):
    # ASCII boundaries allow Chinese text immediately next to an English skill.
    return re.compile(r"(?<![A-Za-z0-9_])" + re.escape(alias) + r"(?![A-Za-z0-9_+])", re.I)


def taxonomy():
    data = json.loads((ROOT / "config/skills.json").read_text())
    return [(item["name"], [pattern(a) for a in item["aliases"]]) for item in data]


PREFERRED = re.compile(r"preferred|nice.to.have|a plus|bonus|stand out|优先|加分|更佳|尤佳", re.I)
REQUIRED = re.compile(r"required|requirements|minimum qualifications|basic qualifications|must\b|what we need|任职要求|职位要求|岗位要求|基本要求|必备|必须|熟练|掌握|精通", re.I)
RESPONSIBILITY = re.compile(r"responsibilit|what you.ll (?:be )?do|job description|工作职责|岗位职责|职位描述", re.I)
NEGATED = re.compile(r"not required|no .{0,35}(?:required|necessary)|无需|不要求|不需要", re.I)


def extract_skills(description):
    """Return sentence-level evidence. Never infer from the job title."""
    rules = taxonomy()
    found = {}
    section = "unknown"
    for line in plain(description).splitlines():
        if len(line) < 100:
            # A heading must not be an ordinary sentence containing a skill.
            is_heading = not any(p.search(line) for _, pats in rules for p in pats)
            if is_heading:
                if PREFERRED.search(line):
                    section = "preferred"
                elif REQUIRED.search(line):
                    section = "required"
                elif RESPONSIBILITY.search(line):
                    section = "mentioned"
        for sentence in re.split(r"(?<=[。；;])\s*|(?<=[.!?])\s+(?=[A-Z])", line):
            if not sentence:
                continue
            level = section
            if NEGATED.search(sentence):
                level = "mentioned"
            elif PREFERRED.search(sentence):
                level = "preferred"
            elif REQUIRED.search(sentence):
                level = "required"
            for name, pats in rules:
                if any(p.search(sentence) for p in pats):
                    evidence = {"text": sentence, "requirement": level}
                    found.setdefault(name, [])
                    if evidence not in found[name]:
                        found[name].append(evidence)
    return [{"name": name, "evidence": evidence} for name, evidence in sorted(found.items())]


CATEGORIES = {
    "ai": r"machine learning|deep learning|reinforcement learning|generative ai|\bLLM\b|artificial intelligence|机器学习|深度学习|强化学习|大模型|人工智能|算法工程",
    "vision": r"computer vision|image processing|object detection|image segmentation|计算机视觉|图像|视觉|目标检测",
    "3d": r"\bSLAM\b|\bNeRF\b|3D|reconstruction|point cloud|Gaussian splatting|三维|重建|点云|空间感知",
    "ece": r"embedded|firmware|robotics|\bCUDA\b|GPU (?:software|computing|kernel)|systems software|嵌入式|固件|机器人|底层软件|驱动开发|高性能计算",
}


def categories(title, description):
    text = title + "\n" + plain(description)
    return [key for key, regex in CATEGORIES.items() if re.search(regex, text, re.I)]


def seniority(title, description="", hint=""):
    text = f"{title} {hint}"
    if re.search(r"\bintern(?:ship)?s?\b|实习", text, re.I):
        return "intern"
    if re.search(r"new (?:college )?grad|graduate|early.career|entry.level|junior|校招|校园|应届|毕业生|初级", text, re.I):
        return "graduate"
    if re.search(r"\bsenior\b|\bstaff\b|\bprincipal\b|\bdirector\b|\bmanager\b|高级|资深|专家|总监", title, re.I):
        return "experienced"
    # Avoid inferring graduate eligibility merely from a degree requirement.
    if re.search(r"new graduates? (?:are )?welcome|应届生(?:亦可|优先|可申请)", description, re.I):
        return "graduate"
    return "unknown"


def markets(location):
    result = []
    if re.search(r"\bUS\b|\bUSA\b|United States|美国", location, re.I):
        result.append("US")
    if re.search(r"\bChina\b|中国|北京|上海|深圳|杭州|广州|成都|武汉|南京|西安|苏州|合肥|东莞|重庆|天津|珠海|长沙", location, re.I):
        result.append("CN")
    return result


def enrich(raw):
    description = plain(raw.pop("description"))
    raw["categories"] = categories(raw["title"], description)
    raw["seniority"] = seniority(raw["title"], description, raw.pop("level_hint", ""))
    raw["markets"] = markets(raw["location"])
    raw["skills"] = extract_skills(description)
    raw["description_hash"] = hashlib.sha256(description.encode()).hexdigest()
    return raw
