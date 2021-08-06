from django.test import TestCase
from main.views import save_recent_bb
from main.models import SubRubric, SuperRubric, AdvUser, Bb

class SaveRecentTest(TestCase):
    def test_save_recent_bbs(self):
        testuser1 = AdvUser.objects.create_user(username = 'testuser1', password = 'Test1111')
        testrubric1 = SubRubric.objects.create(name = 'cars')
        bb1 = Bb.objects.create(title = 'bb1', author = testuser1, rubric = testrubric1)
        bb2 = Bb.objects.create(title = 'bb2', author = testuser1, rubric = testrubric1)
        bb3 = Bb.objects.create(title = 'bb3', author = testuser1, rubric = testrubric1)
        bb4 = Bb.objects.create(title = 'bb4', author = testuser1, rubric = testrubric1)
        save_recent_bb(user=testuser1, bb=bb1)
        save_recent_bb(user=testuser1, bb=bb2)
        save_recent_bb(user=testuser1, bb=bb3)
        save_recent_bb(user=testuser1, bb=bb4)
        self.assertEqual( [ bb.bb for bb in testuser1.recentbbs_set.all() ], [bb4, bb3, bb2] )

