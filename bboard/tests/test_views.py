from django.test import TestCase

import json
from main.models import SubRubric, SuperRubric, AdvUser, Bb
from main.views import save_recent_bb
from main.forms import SearchForm
from django.urls import reverse

class IndexViewTest(TestCase):

    @classmethod
    def setUpTestData(self):
        superrub = SuperRubric.objects.create(name = 'sup')
        testrubric = SubRubric.objects.create(name = 'cars', super_rubric = superrub)
        testuser1 = AdvUser.objects.create_user(username = 'Alex', password = 'Test1111')
        testuser2 = AdvUser.objects.create_user(username = 'Alex2', password = 'Test2222')
        number_of_bbs = 11
        for bb_num in range(number_of_bbs):
            bb_name = 'car' if bb_num % 2 else 'book'
            Bb.objects.create(title = bb_name + str(bb_num),
                          author = testuser1 if bb_num % 2 else testuser2,
                          rubric = testrubric)

    def test_view_url_exists_at_desired_location(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
    
    def test_view_url_accessible_by_name(self):
        resp = self.client.get(reverse('main:index'))
        self.assertEqual(resp.status_code, 200)

    def test_view_uses_correct_template(self):
        resp = self.client.get(reverse('main:index'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'main/index.html')

    def test_all_bbs_in_list(self):
        resp = self.client.get(reverse('main:index'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['bbs']), len(Bb.objects.all()))

    def test_bbs_ordering(self):
        resp = self.client.get(reverse('main:index'))
        self.assertEqual(resp.status_code, 200)
        tmp = None
        bbs = resp.context['bbs']
        for bb in bbs:
            if tmp == None:
                tmp = bb
            else:
                self.assertTrue(bb.created_at <= tmp.created_at)
                tmp = bb

    def test_search(self):
        rub = SubRubric.objects.get(name='cars').id
        data = {'rubric': rub, 'keyword': ['car']}
        resp = self.client.post("", data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['bbs']), 5)

    def test_bbs_search_ordering(self):
        rub = SubRubric.objects.get(name='cars')
        data = {'rubric': rub.id, 'keyword': ['car']}
        resp = self.client.post("", data)
        self.assertEqual(resp.status_code, 200)
        tmp = None
        for bb in resp.context['bbs']:
            if tmp == None:
                tmp = bb
            else:
                self.assertTrue(bb.created_at <= tmp.created_at)
                tmp = bb

    def test_search_capitalize(self):
        rub = SubRubric.objects.get(name='cars')
        data = {'rubric': rub.id, 'keyword': ['Car']}
        resp = self.client.post("", data)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(rub.id%2 == 0)
        self.assertEqual(len(resp.context['bbs']), 5)


class OtherPageViewTest(TestCase):

    def test_other_page_url_exists_at_desired_location(self):
        resp = self.client.get('/about/')
        self.assertEqual(resp.status_code, 200)

    def test_view_uses_correct_template(self):
        resp = self.client.get('/about/')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'main/about.html')

    def test_other_page_404(self):
        resp = self.client.get('/notaurl/')
        self.assertEqual(resp.status_code, 404)

class LoginViewTest(TestCase):

    def test_login_exists_at_desired_location(self):
        resp = self.client.get('/login/')
        self.assertEqual(resp.status_code, 200)

    def test_view_uses_correct_template(self):
        resp = self.client.get(reverse('main:login'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'main/login.html')

class ProfileViewTest(TestCase):
    def setUp(self):
        test_user1 = AdvUser.objects.create_user(username = 'testuser1',
                                                 password = 'Test1111')
        test_user2 = AdvUser.objects.create_user(username = 'testuser2',
                                                 password = 'Test2222')
        superrub = SuperRubric.objects.create(name = 'sup')
        testrubric = SubRubric.objects.create(name = 'cars', super_rubric = superrub)
        number_of_bbs = 5
        for bb_num in range(number_of_bbs):
            bb_name = 'car' if bb_num % 2 else 'book'
            Bb.objects.create(title = bb_name + str(bb_num),
                          author = test_user1 if bb_num % 2 == 0 else test_user2,
                          rubric = SubRubric.objects.get(name = 'cars'))

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('main:profile'))
        self.assertRedirects(resp, '/accounts/login/?next=/accounts/profile/')

    def test_logged_in_profile_uses_correct_template(self):
        self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get(reverse('main:profile'))
        self.assertTemplateUsed('main/profile_bbs.html')

    def test_profile_only_your_bbs(self):
        self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get(reverse('main:profile'))
        user = resp.context['user']
        self.assertEqual(str(user), 'testuser1')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('bbs' in resp.context)
        bbs = resp.context['bbs'].select_related('author')
        self.assertEqual(len(bbs), 3)
        for bb in bbs:
            self.assertEqual(bb.author.id, user.id)

    def test_profile_bbs_ordering(self):
        self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get(reverse('main:profile'))
        self.assertEqual(resp.status_code, 200)
        tmp = None
        for bb in resp.context['bbs']:
            if tmp == None:
                tmp = bb
            else:
                self.assertTrue(bb.created_at <= tmp.created_at)
                tmp = bb


class ProfileLikedViewTest(TestCase):
    def setUp(self):
        test_user1 = AdvUser.objects.create_user(username = 'testuser1',
                                                 password = 'Test1111')
        test_user1.save()
        test_user2 = AdvUser.objects.create_user(username = 'testuser2',
                                                 password = 'Test2222')
        test_user2.save()
        superrub = SuperRubric.objects.create(name = 'sup')
        superrub.save()
        testrubric = SubRubric.objects.create(name = 'cars', super_rubric = superrub)
        testrubric.save()
        number_of_bbs = 5
        superrub = SubRubric.objects.get(name = 'cars')
        for bb_num in range(number_of_bbs):
            bb_name = 'car' if bb_num % 2 else 'book'
            bb = Bb.objects.create(title = bb_name + str(bb_num), content='red',
                                   price = 20000, contacts = 'Call',
                                   author = test_user1 if bb_num % 2 == 0 else test_user2,
                                   rubric = superrub)
            bb.likes.add(test_user2 if bb_num%2 == 0 else test_user1)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('main:profile_liked'))
        self.assertRedirects(resp, '/accounts/login/?next=/accounts/profile/liked/')

    def test_logged_in_profile_uses_correct_template(self):
        self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get(reverse('main:profile_liked'))
        self.assertTemplateUsed('main/profile_liked.html')

    def test_profile_only_your_liked_bbs(self):
        self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get(reverse('main:profile_liked'))
        user = resp.context['user']
        self.assertEqual(str(user), 'testuser1')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('bbs' in resp.context)
        bbs = resp.context['bbs']
        self.assertEqual(len(bbs), 2)
        for bb in user.bb_post.all():
            self.assertTrue(bb in bbs)

    def test_liked_bb_ordering(self):
        self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get(reverse('main:profile_liked'))
        self.assertEqual(resp.status_code, 200)
        tmp = None
        for bb in resp.context['bbs']:
            if tmp == None:
                tmp = bb
            else:
                self.assertTrue(bb.created_at <= tmp.created_at)
                tmp = bb


class BbLogoutViewTest(TestCase):
    def setUp(self):
        test_user1 = AdvUser.objects.create_user(username = 'testuser1',
                                                 password = 'Test1111')
    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('main:profile_liked'))
        self.assertRedirects(resp, '/accounts/login/?next=/accounts/profile/liked/')

    def test_logout_exists_at_desired_location(self):
       self.client.login(username = 'testuser1', password = 'Test1111')
       resp = self.client.get('/accounts/logout/')
       self.assertEqual(resp.status_code, 200)

    def test_view_url_accessible_by_name(self):
        self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get(reverse('main:logout'))
        self.assertEqual(resp.status_code, 200)

    def test_logout_view_uses_correct_template(self):
        self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get(reverse('main:logout'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'main/index.html')


class ChangeUserInfoViewTest(TestCase):
    def setUp(self):
        test_user1 = AdvUser.objects.create_user(username = 'testuser1',
                                                 password = 'Test1111')
    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('main:profile_liked'))
        self.assertRedirects(resp, '/accounts/login/?next=/accounts/profile/liked/')

    def test_logout_exists_at_desired_location(self):
       self.client.login(username = 'testuser1', password = 'Test1111')
       resp = self.client.get('/accounts/profile/change/')
       self.assertEqual(resp.status_code, 200)

    def test_view_url_accessible_by_name(self):
        self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get(reverse('main:profile_change'))
        self.assertEqual(resp.status_code, 200)


class BBPasswordChangeViewTest(TestCase):
    def setUp(self):
        test_user1 = AdvUser.objects.create_user(username = 'testuser1',
                                                 password = 'Test1111')

    def test_view_url_accessible_by_name(self):
        self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get(reverse('main:password_change'))
        self.assertEqual(resp.status_code, 200)


    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('main:password_change'))
        self.assertRedirects(resp, '/accounts/login/?next=/accounts/password/change/')

    def test_view_url_exists_at_desired_location(self):
        self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get(reverse('main:password_change'))
        self.assertEqual(resp.status_code, 200)


class RegisterUserViewTest(TestCase):
    def test_view_url_accessible_by_name(self):
        resp = self.client.get(reverse('main:register'))
        self.assertEqual(resp.status_code, 200)

    def test_view_url_exists_at_desired_location(self):
        resp = self.client.get(reverse('main:register'))
        self.assertEqual(resp.status_code, 200)


class RegisterUserDoneViewTest(TestCase):
    def test_view_url_accessible_by_name(self):
        resp = self.client.get(reverse('main:register_done'))
        self.assertEqual(resp.status_code, 200)

    def test_view_url_exists_at_desired_location(self):
        resp = self.client.get(reverse('main:register_done'))
        self.assertEqual(resp.status_code, 200)


class DeleteUserViewTest(TestCase):
    def setUp(self):
        test_user1 = AdvUser.objects.create_user(username = 'testuser1',
                                                 password = 'Test1111')

    def test_view_url_accessible_by_name(self):
        self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get(reverse('main:profile_delete'))
        self.assertEqual(resp.status_code, 200)

    def test_view_url_exists_at_desired_location(self):
        self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get(reverse('main:profile_delete'))
        self.assertEqual(resp.status_code, 200)


class ByRubricViewTest(TestCase):
    @classmethod
    def setUpTestData(self):
        superrub = SuperRubric.objects.create(name = 'sup')
        testrubric1 = SubRubric.objects.create(name = 'cars', super_rubric = superrub)
        testrubric2 = SubRubric.objects.create(name = 'books', super_rubric = superrub)
        testuser1 = AdvUser.objects.create_user(username = 'Alex', password = 'Test1111')
        testuser2 = AdvUser.objects.create_user(username = 'Alex2', password = 'Test2222')
        number_of_bbs = 5
        for bb_num in range(number_of_bbs):
            bb_name = f'car {bb_num}' if bb_num % 2 else 'book'
            Bb.objects.create(title = bb_name + str(bb_num),
                          author = testuser1 if bb_num % 2 else testuser2,
                          rubric = testrubric1 if bb_num % 2 else testrubric2)
    def test_view_url_exists_at_desired_location(self):
        resp = self.client.get(reverse('main:by_rubric', kwargs = {'pk': 2}))
        self.assertEqual(resp.status_code, 200)
    
    def test_view_url_accessible_by_name(self):
        resp = self.client.get(reverse('main:by_rubric', kwargs = {'pk': 2}))
        self.assertEqual(resp.status_code, 200)

    def test_view_uses_correct_template(self):
        resp = self.client.get(reverse('main:by_rubric', kwargs = {'pk': 2}))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'main/by_rubric.html')

    def test_rubric_bbs_in_list(self):
        testrubric1_id = SubRubric.objects.get(name = 'cars').id
        resp = self.client.get(reverse('main:by_rubric', kwargs = {'pk': 2}))
        self.assertEqual(resp.status_code, 200)
        bbs =  resp.context['bbs'].select_related('rubric')
        self.assertEqual(len(bbs), 2)
        for bb in bbs:
            self.assertEqual(bb.rubric.id, testrubric1_id)

    def test_bbs_ordering(self):
        resp = self.client.get(reverse('main:by_rubric', kwargs = {'pk': 2}))
        self.assertEqual(resp.status_code, 200)
        tmp = None
        bbs = resp.context['bbs']
        for bb in bbs:
            if tmp == None:
                tmp = bb
            else:
                self.assertTrue(bb.created_at <= tmp.created_at)
                tmp = bb

    def test_search(self):
        rub = SubRubric.objects.get(name='cars').id
        data = {'rubric': rub, 'keyword': ['1']}
        resp = self.client.post((reverse('main:by_rubric', kwargs = {'pk': 2})), data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['bbs']), 1)

    def test_bbs_search_ordering(self):
        rub = SubRubric.objects.get(name='cars')
        data = {'rubric': rub.id, 'keyword': ['car']}
        resp = self.client.post((reverse('main:by_rubric', kwargs = {'pk': 2})), data)
        self.assertEqual(resp.status_code, 200)
        tmp = None
        for bb in resp.context['bbs']:
            if tmp == None:
                tmp = bb
            else:
                self.assertTrue(bb.created_at <= tmp.created_at)
                tmp = bb

    def test_search_capitalize(self):
        rub = SubRubric.objects.get(name='cars')
        data = {'rubric': rub.id, 'keyword': ['Car 1']}
        resp = self.client.post((reverse('main:by_rubric', kwargs = {'pk': 2})), data)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(rub.id%2 == 0)
        self.assertEqual(len(resp.context['bbs']), 1)

class ByRubricViewTest(TestCase):

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