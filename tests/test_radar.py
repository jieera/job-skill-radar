import copy
import json
import unittest
from radar.analysis import extract_skills, seniority, categories, markets, plain
from radar.http import SourceError
from radar.pipeline import merge
from radar.sources import pages, apple_state


def raw(id="demo:1", description="Requirements\nPython and PyTorch required."):
    return {"id":id,"source":"demo","company":"Demo","title":"Machine Learning Intern",
            "location":"US, CA","url":"https://example.org/job/1","posted_at":None,"description":description}


def result(jobs=(), status="ok"):
    return {"id":"demo","name":"Demo","market":"US","url":"https://example.org", "scope":"test", "status":status,"message":"test","jobs":list(jobs)}


class AnalysisTests(unittest.TestCase):
    def skills(self, text):
        return {s["name"]:s["evidence"] for s in extract_skills(text)}

    def test_chinese_aliases(self):
        self.assertEqual(set(self.skills("熟练掌握PyTorch，熟悉神经辐射场和点云。")), {"PyTorch","NeRF","Point clouds"})

    def test_boundaries(self):
        self.assertEqual(set(self.skills("JavaScript C++ GitHub ROS2")), {"JavaScript","C++","ROS"})

    def test_duplicate_alias(self):
        self.assertEqual(len(self.skills("NeRF / Neural Radiance Fields / 神经辐射场")),1)

    def test_required_and_preferred(self):
        skills=self.skills("Minimum qualifications\nPython\nPreferred qualifications\nCUDA")
        self.assertEqual(skills['Python'][0]['requirement'],'required')
        self.assertEqual(skills['CUDA'][0]['requirement'],'preferred')

    def test_explicit_preferred_overrides_section(self):
        self.assertEqual(self.skills("任职要求\n熟悉 CUDA 者优先。")["CUDA"][0]["requirement"],"preferred")

    def test_negation_not_required(self):
        self.assertEqual(self.skills("Python experience is not required.")["Python"][0]["requirement"],"mentioned")

    def test_uncertain_context(self):
        self.assertEqual(self.skills("Python")["Python"][0]["requirement"],"unknown")

    def test_responsibilities(self):
        self.assertEqual(self.skills("工作职责\n使用 Python 分析数据。")["Python"][0]["requirement"],"mentioned")

    def test_html_preserves_evidence_and_ignores_scripts(self):
        self.assertEqual(plain('<p>A &amp; B</p><script>Python</script><li>C++</li>'),'A & B\nC++')

    def test_levels(self):
        self.assertEqual(seniority("Research Intern"),"intern")
        self.assertEqual(seniority("Engineer",hint="应届毕业生"),"graduate")
        self.assertEqual(seniority("Senior ML Engineer"),"experienced")
        self.assertEqual(seniority("Engineer","Bachelor or graduate degree required"),"unknown")

    def test_locations(self):
        self.assertEqual(markets('US, CA · China, Shanghai'),['US','CN'])
        self.assertEqual(markets('Canada, Toronto'),[])

    def test_multilabel(self):
        self.assertEqual(set(categories('Computer vision SLAM intern','Deep learning with CUDA')),{'ai','vision','3d','ece'})


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.initial=merge({},[result([raw()])],'2026-01-01T00:00:00Z')

    def test_deduplication(self):
        self.assertEqual(len(merge({},[result([raw(),raw()])],'now')['jobs']),1)

    def test_two_successful_misses(self):
        first=merge(self.initial,[result()],'day2')
        self.assertTrue(first['jobs'][0]['active'])
        second=merge(first,[result()],'day3')
        self.assertFalse(second['jobs'][0]['active'])

    def test_failure_preserves_jobs_and_timestamp(self):
        after=merge(self.initial,[result(status='error')],'day2')
        self.assertEqual(after['jobs'],self.initial['jobs'])
        self.assertEqual(after['sources'][0]['last_success'],'2026-01-01T00:00:00Z')

    def test_failure_does_not_count_as_absence(self):
        first=merge(self.initial,[result()],'day2')
        failed=merge(first,[result(status='error')],'day3')
        self.assertEqual(failed['jobs'][0]['missing_runs'],1)

    def test_partial_updates_valid_rows_without_expiry(self):
        after=merge(self.initial,[result([raw('demo:2')],status='partial')],'day2')
        self.assertEqual(len(after['jobs']),2)
        self.assertTrue(all(j['missing_runs']==0 for j in after['jobs']))

    def test_reopened_job_and_first_seen(self):
        closed=merge(merge(self.initial,[result()],'day2'),[result()],'day3')
        opened=merge(closed,[result([raw()])],'day4')['jobs'][0]
        self.assertTrue(opened['active']);self.assertEqual(opened['first_seen'],'2026-01-01T00:00:00Z')

    def test_description_change_reextracts(self):
        after=merge(self.initial,[result([raw(description='Requirements\nCUDA required.')])],'day2')
        self.assertEqual([s['name'] for s in after['jobs'][0]['skills']],['CUDA'])
        self.assertEqual(after['jobs'][0]['updated_at'],'day2')

    def test_no_title_based_skills(self):
        job=merge({},[result([raw(description='Work with a collaborative research team.')])],'now')['jobs'][0]
        self.assertEqual(job['skills'],[])

    def test_does_not_mutate_input(self):
        before=copy.deepcopy(self.initial);merge(self.initial,[result()],'day2')
        self.assertEqual(self.initial,before)


class SourceTests(unittest.TestCase):
    def test_paginated_total_only_on_first_page(self):
        responses=[{'rows':[{'id':'a'},{'id':'b'}],'total':3},{'rows':[{'id':'c'}],'total':0}]
        calls=[]
        def fetch(offset,limit):
            calls.append(offset);return responses.pop(0)
        self.assertEqual(len(list(pages(fetch,'rows','total','id',2))),3)
        self.assertEqual(calls,[0,2])

    def test_repeated_page_fails(self):
        with self.assertRaises(SourceError):
            list(pages(lambda *_:{'rows':[{'id':'a'}],'total':3},'rows','total','id'))

    def test_premature_empty_fails(self):
        with self.assertRaises(SourceError):
            list(pages(lambda *_:{'rows':[],'total':3},'rows','total','id'))

    def test_legitimate_empty(self):
        self.assertEqual(list(pages(lambda *_:{'rows':[],'total':0},'rows','total','id')),[])

    def test_apple_parser_does_not_execute_javascript(self):
        state={'loaderData':{'search':{'totalRecords':0}}}
        encoded=json.dumps(json.dumps(state))
        self.assertEqual(apple_state('window.__staticRouterHydrationData = JSON.parse('+encoded+');'),state['loaderData'])
        with self.assertRaises(SourceError):apple_state('<html>Sign in</html>')


if __name__=='__main__':unittest.main()
