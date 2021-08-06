from django.test import TestCase
import pathlib
from pathlib import Path 
from django.core.files.uploadedfile import SimpleUploadedFile
from main.models import SubRubric, SuperRubric, AdvUser, Bb
from main.forms import SearchForm
from django.urls import reverse
from main.utilities import get_timestamp_path

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
        resp = self.client.get('/accounts/password/change/')
        self.assertEqual(resp.status_code, 200)


class RegisterUserViewTest(TestCase):
    def test_view_url_accessible_by_name(self):
        resp = self.client.get(reverse('main:register'))
        self.assertEqual(resp.status_code, 200)

    def test_view_url_exists_at_desired_location(self):
        resp = self.client.get('/accounts/register/')
        self.assertEqual(resp.status_code, 200)


class RegisterUserDoneViewTest(TestCase):
    def test_view_url_accessible_by_name(self):
        resp = self.client.get(reverse('main:register_done'))
        self.assertEqual(resp.status_code, 200)

    def test_view_url_exists_at_desired_location(self):
        resp = self.client.get('/accounts/register/done/')
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
        resp = self.client.get('/accounts/profile/delete/')
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
        resp = self.client.get('/2/')
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


class DetailViewTest(TestCase):
    @classmethod
    def setUpTestData(self):
        superrub = SuperRubric.objects.create(name = 'sup')
        testrubric1 = SubRubric.objects.create(name = 'cars', super_rubric = superrub)
        testuser1 = AdvUser.objects.create_user(username = 'Alex', password = 'Test1111')
        Bb.objects.create(title = 'car',
                          author = testuser1,
                          rubric = testrubric1)
    def test_view_url_exists_at_desired_location(self):
        bb = Bb.objects.get(title = 'car')
        resp = self.client.get(f'/{bb.rubric.id}/{bb.id}/')
        self.assertEqual(resp.status_code, 200)
    
    def test_view_url_accessible_by_name(self):
        bb = Bb.objects.get(title = 'car')
        resp = self.client.get(reverse('main:detail', kwargs = {'rubric_pk': bb.rubric.id, 'pk': bb.id}))
        self.assertEqual(resp.status_code, 200)

    def test_view_uses_correct_template(self):
        bb = Bb.objects.get(title = 'car')
        resp = self.client.get(reverse('main:detail', kwargs = {'rubric_pk': bb.rubric.id, 'pk': bb.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'main/detail.html')

    def test_detail_correct_bb(self):
        bb = Bb.objects.get(title = 'car')
        resp = self.client.get(reverse('main:detail', kwargs = {'rubric_pk': bb.rubric.id, 'pk': bb.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['bb'].id, bb.id)

    def test_additional_images(self):
        bb = Bb.objects.get(title = 'car')
        resp = self.client.get(reverse('main:detail', kwargs = {'rubric_pk': bb.rubric.id, 'pk': bb.id}))
        self.assertEqual(resp.status_code, 200)
        for ai in resp.context['ais']:
            self.assertEqual(ai.bb, bb)

    def test_related_bbs(self):
        bb = Bb.objects.get(title = 'car')
        resp = self.client.get(reverse('main:detail', kwargs = {'rubric_pk': bb.rubric.id, 'pk': bb.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(bb not in resp.context['bbs'])

    def test_views_counter(self):
        bb = Bb.objects.get(title = 'car')
        self.assertEqual(bb.views, 0)
        resp = self.client.get(reverse('main:detail', kwargs = {'rubric_pk': bb.rubric.id, 'pk': bb.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Bb.objects.get(id=bb.id).views, 1)


class ProfileBbDetailTest(TestCase):
    @classmethod
    def setUpTestData(self):
        superrub = SuperRubric.objects.create(name = 'sup')
        testrubric1 = SubRubric.objects.create(name = 'cars', super_rubric = superrub)
        testuser1 = AdvUser.objects.create_user(username = 'testuser1', password = 'Test1111')
        testuser2 = AdvUser.objects.create_user(username = 'testuser2', password = 'Test2222')
        Bb.objects.create(title = 'user1bb',
                          author = testuser1,
                          rubric = testrubric1)
        Bb.objects.create(title = 'user2bb',
                          author = testuser2,
                          rubric = testrubric1)
    def test_view_url_exists_at_desired_location(self):
        bb = Bb.objects.get(title = 'user1bb')
        resp = self.client.get(f'/{bb.rubric.id}/{bb.id}/')
        self.assertEqual(resp.status_code, 200)
    
    def test_view_url_accessible_by_name(self):
        bb = Bb.objects.get(title = 'user1bb')
        resp = self.client.get(reverse('main:detail', kwargs = {'rubric_pk': bb.rubric.id, 'pk': bb.id}))
        self.assertEqual(resp.status_code, 200)

    def test_view_uses_correct_template(self):
        bb = Bb.objects.get(title = 'user1bb')
        resp = self.client.get(reverse('main:detail', kwargs = {'rubric_pk': bb.rubric.id, 'pk': bb.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'main/detail.html')


class BbAddTest(TestCase):
    @classmethod
    def setUpTestData(self):
       test_user1 = AdvUser.objects.create_user(username = 'testuser1',
                                                password = 'Test1111')
       superrub = SuperRubric.objects.create(name = 'sup')
       testrubric1 = SubRubric.objects.create(name = 'cars', super_rubric = superrub)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('main:profile_bb_add'))
        self.assertRedirects(resp, '/accounts/login/?next=/accounts/profile/add/')

    def test_view_url_exists_at_desired_location(self):
        login = self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get('/accounts/profile/add/')
        self.assertEqual(resp.status_code, 200)
    
    def test_view_url_accessible_by_name(self):
        login = self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get(reverse('main:profile_bb_add'))
        self.assertEqual(resp.status_code, 200)

    def test_view_uses_correct_template(self):
        login = self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get(reverse('main:profile_bb_add'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'main/profile_bb_add.html')

    def test_bb_added(self):
        login = self.client.login(username = 'testuser1', password = 'Test1111')
        rub = SubRubric.objects.get(name='cars').id
        author = AdvUser.objects.get(username='testuser1').id
        data = {'rubric': rub, 'title': 'car', 'content': 'red', 'price': 20000,
                'contacts': 'call', 'image': get_timestamp_path(author, 'img'),
                'author': author}
        resp = self.client.post(reverse('main:profile_bb_add'), data)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Bb.objects.get(title = 'car'))
        
    def test_bb_additional_images_added(self):
        login = self.client.login(username = 'testuser1', password = 'Test1111')
        rub = SubRubric.objects.get(name='cars').id
        author = AdvUser.objects.get(username='testuser1').id
        image = "static\test1.jpg"
        data = {'rubric': rub, 'title': 'car', 'content': 'red', 'price': 20000,
                    'contacts': 'call', 'image': get_timestamp_path(author, 'img'),
                    'author': author, 'file': image}
        resp = self.client.post(reverse('main:profile_bb_add'), data)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Bb.objects.get(title = 'car'))


class BbChangeTest(TestCase):
    @classmethod
    def setUpTestData(self):
       self.testuser1 = AdvUser.objects.create_user(username = 'testuser1',
                                                password = 'Test1111')
       self.testuser2 = AdvUser.objects.create_user(username = 'testuser2',
                                                password = 'Test2222')
       superrub = SuperRubric.objects.create(name = 'sup')
       testrubric1 = SubRubric.objects.create(name = 'cars', super_rubric = superrub)
       testrubric2 = SubRubric.objects.create(name = 'books', super_rubric = superrub)
       self.bb_id = Bb.objects.create(title = 'car', content='red',
                                   price = 20000, contacts = 'Call',
                                   author = self.testuser1,
                                   rubric = superrub).id

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('main:profile_bb_change', kwargs = {'pk': 1}))
        self.assertRedirects(resp, '/accounts/login/?next=/accounts/profile/change/1/')

    def test_404_if_wrong_user(self):
        login = self.client.login(username = 'testuser2', password = 'Test2222')
        resp = self.client.get('/accounts/profile/change/1/')
        self.assertEqual(resp.status_code, 404)

    def test_view_url_exists_at_desired_location(self):
        login = self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get('/accounts/profile/change/1/')
        self.assertEqual(resp.status_code, 200)
    
    def test_view_url_accessible_by_name(self):
        login = self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get(reverse('main:profile_bb_change', kwargs = {'pk': 1}))
        self.assertEqual(resp.status_code, 200)

    def test_view_uses_correct_template(self):
        login = self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get(reverse('main:profile_bb_change', kwargs = {'pk': 1}))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'main/profile_bb_change.html')

    def test_bb_changed(self):
        login = self.client.login(username = 'testuser1', password = 'Test1111')
        rub = SubRubric.objects.get(name='books').id
        author = AdvUser.objects.get(username='testuser2').id
        data = {'rubric': rub, 'title': 'car2', 'content': 'red2', 'price': 22000,
                'contacts': 'call2', 'author': author}
        resp = self.client.post(reverse('main:profile_bb_change', kwargs = {'pk': 1}), data)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Bb.objects.get(id=self.bb_id).title, 'car2')
        self.assertTrue(Bb.objects.get(id=self.bb_id).content, 'red2')
        self.assertTrue(Bb.objects.get(id=self.bb_id).price, 22000)
        self.assertTrue(Bb.objects.get(id=self.bb_id).contacts, 'call2')
        self.assertTrue(Bb.objects.get(id=self.bb_id).author, self.testuser2)


class BbDeleteTest(TestCase):
    @classmethod
    def setUpTestData(self):
       self.testuser1 = AdvUser.objects.create_user(username = 'testuser1',
                                                password = 'Test1111')
       self.testuser2 = AdvUser.objects.create_user(username = 'testuser2',
                                                password = 'Test2222')
       superrub = SuperRubric.objects.create(name = 'sup')
       testrubric1 = SubRubric.objects.create(name = 'cars', super_rubric = superrub)
       self.bb_id = Bb.objects.create(title = 'car', content='red',
                                   price = 20000, contacts = 'Call',
                                   author = self.testuser1,
                                   rubric = superrub).id

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('main:profile_bb_delete', kwargs = {'pk': 1}))
        self.assertRedirects(resp, '/accounts/login/?next=/accounts/profile/delete/1/')

    def test_404_if_wrong_user(self):
        login = self.client.login(username = 'testuser2', password = 'Test2222')
        resp = self.client.get('/accounts/profile/delete/1/')
        self.assertEqual(resp.status_code, 404)

    def test_view_url_exists_at_desired_location(self):
        login = self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get('/accounts/profile/delete/1/')
        self.assertEqual(resp.status_code, 200)
    
    def test_view_url_accessible_by_name(self):
        login = self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get(reverse('main:profile_bb_delete', kwargs = {'pk': 1}))
        self.assertEqual(resp.status_code, 200)

    def test_view_uses_correct_template(self):
        login = self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get(reverse('main:profile_bb_delete', kwargs = {'pk': 1}))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'main/profile_bb_delete.html')

    def test_bb_deleted(self):
        login = self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.post(reverse('main:profile_bb_delete', kwargs = {'pk': 1}))
        self.assertRedirects(resp, reverse('main:profile'), status_code=302, 
        target_status_code=200, fetch_redirect_response=True)
        self.assertFalse(Bb.objects.filter(id=self.bb_id))


class ForeignUserTest(TestCase):
    def setUp(self):
        self.testuser1 = AdvUser.objects.create_user(username = 'testuser1',
                                                 password = 'Test1111')
        self.testuser2 = AdvUser.objects.create_user(username = 'testuser2',
                                                 password = 'Test2222')
        superrub = SuperRubric.objects.create(name = 'sup')
        testrubric = SubRubric.objects.create(name = 'cars', super_rubric = superrub)
        number_of_bbs = 5
        for bb_num in range(number_of_bbs):
            bb_name = 'car' if bb_num % 2 else 'book'
            Bb.objects.create(title = bb_name + str(bb_num),
                          author = self.testuser1 if bb_num % 2 == 0 else self.testuser2,
                          rubric = SubRubric.objects.get(name = 'cars'))

    def test_redirect_to_profile_if_it_is_yourself(self):
        login = self.client.login(username = 'testuser1', password = 'Test1111')
        resp = self.client.get('main:foreign_user', kwargs = {'pk': self.testuser1.id})
        self.assertTemplateUsed('main/profile_bbs.html')

    def test_view_url_exists_at_desired_location(self):
        resp = self.client.get(f'/user/{self.testuser1.id}/')
        self.assertEqual(resp.status_code, 200)
    
    def test_view_url_accessible_by_name(self):
        resp = self.client.get(reverse('main:foreign_user', kwargs = {'pk': self.testuser1.id}))
        self.assertEqual(resp.status_code, 200)

    def test_view_uses_correct_template(self):
        login = self.client.login(username = 'testuser2', password = 'Test2222')
        resp = self.client.get(reverse('main:foreign_user', kwargs = {'pk': self.testuser1.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'main/foreign_user.html')

    def test_user_bbs(self):
        resp = self.client.get(reverse('main:foreign_user', kwargs = {'pk': self.testuser1.id}))
        self.assertEqual(resp.status_code, 200)
        bbs = resp.context['bbs']
        self.assertEqual(len(bbs), len(Bb.objects.filter(author=self.testuser1)))
        for bb in bbs:
            self.assertEqual(bb.author, self.testuser1)

    def test_bbs_ordering(self):
        resp = self.client.get(reverse('main:foreign_user', kwargs = {'pk': self.testuser1.id}))
        self.assertEqual(resp.status_code, 200)
        tmp = None
        bbs = resp.context['bbs']
        for bb in bbs:
            if tmp == None:
                tmp = bb
            else:
                self.assertTrue(bb.created_at <= tmp.created_at)
                tmp = bb
    

class BySuperRubricTest(TestCase):
    @classmethod
    def setUpTestData(self):
        self.superrub1 = SuperRubric.objects.create(name = 'cars')
        self.superrub2 = SuperRubric.objects.create(name = 'books')
        self.testrubric1 = SubRubric.objects.create(name = 'cars1', super_rubric = self.superrub1)
        self.testrubric2 = SubRubric.objects.create(name = 'cars2', super_rubric = self.superrub1)
        self.testrubric3 = SubRubric.objects.create(name = 'books1', super_rubric = self.superrub2)
        self.testrubric4 = SubRubric.objects.create(name = 'books2', super_rubric = self.superrub2)
        testuser1 = AdvUser.objects.create_user(username = 'testuser1', password = 'Test1111')
        testuser2 = AdvUser.objects.create_user(username = 'testuser2', password = 'Test2222')
        number_of_bbs = 15
        rubric = None
        for bb_num in range(number_of_bbs):
            if bb_num % 4 == 0:
                rubric = self.testrubric1
            elif bb_num % 4 == 1:
                rubric = self.testrubric2
            elif bb_num % 4 == 2:
                rubric = self.testrubric3
            else:
                rubric = self.testrubric4
            bb_name = f'car {bb_num}' if bb_num % 2 else 'book'
            Bb.objects.create(title = bb_name + str(bb_num),
                          author = testuser1 if bb_num % 2 else testuser2,
                          rubric =rubric)
    def test_view_url_exists_at_desired_location(self):
        resp = self.client.get(f'/super/{self.superrub1.id}/')
        self.assertEqual(resp.status_code, 200)
    
    def test_view_url_accessible_by_name(self):
        resp = self.client.get(reverse('main:by_superrubric',
                                       kwargs = {'pk': self.superrub1.id}))
        self.assertEqual(resp.status_code, 200)

    def test_view_uses_correct_template(self):
        resp = self.client.get(reverse('main:by_superrubric',
                                       kwargs = {'pk': self.superrub1.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'main/index.html')

    def test_rubric_bbs_in_list(self):
        resp = self.client.get(reverse('main:by_superrubric',
                                       kwargs ={'pk': self.superrub1.id}))
        self.assertEqual(resp.status_code, 200)
        bbs =  resp.context['bbs'].select_related('rubric')
        self.assertEqual(len(bbs), 8)
        for bb in bbs:
            self.assertTrue(bb.rubric in (self.testrubric1,
                                                      self.testrubric2) )
