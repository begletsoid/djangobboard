from django.test import TestCase, RequestFactory

from main.models import AdvUser, Bb, Rubric, SuperRubric, AdditionalImage

class AdvUserModelTest(TestCase):

    def setUp(self):
        testrubric = Rubric.objects.create(name = 'cars')
        testuser = AdvUser.objects.create(is_activated = True, send_messages = True,
                               username = 'Alex', first_name = 'Alexander',
                               last_name = 'Smith', email = 'alex@gmail.com')
        testbb = Bb.objects.create(title = 'car', content='red', price = 20000,
                          contacts = 'Call', author = testuser, rubric = testrubric)

    def test_user_get_absolute_url(self):
        user = AdvUser.objects.get(id=1)
        self.assertEqual(user.get_absolute_url(), 'user/1')

    def test_user_delete(self):
        user = AdvUser.objects.get(id=1)
        user.delete()
        self.assertEqual(len(Bb.objects.all()), 0)


class RubricModelTest(TestCase):
    def setUp(self):
        testrubric1 = Rubric.objects.create(name = '1cars', order = 1)
        testrubric2 = Rubric.objects.create(name = '2cars', order = 3)
        testrubric3 = Rubric.objects.create(name = '3cars', order = 2)

    def test_rubric_get_absolute_url(self):
        rubric = Rubric.objects.get(id=2)
        self.assertEqual(rubric.get_absolute_url(), '2')

    def test_rubric_order(self):
        self.assertEqual(list(Rubric.objects.all())[1].name, '3cars')


class SuperRubricModelTest(TestCase):
    def setUp(self):
        superrubric = SuperRubric.objects.create(name='super')
        testrubric1 = Rubric.objects.create(name = 'rubric', super_rubric = superrubric)
        testrubric2 = Rubric.objects.create(name = 'rubric2', super_rubric = superrubric)
        testrubric3 = Rubric.objects.create(name = 'sup',)
        testrubric3 = Rubric.objects.create(name = 'sup2',)

    def test_super_rubric_objects(self):
        self.assertEqual(len(SuperRubric.objects.all()), 3)
        for r in SuperRubric.objects.all():
            self.assertEqual(r.super_rubric, None)

class BbModelTest(TestCase):
    def setUp(self):
        testrubric = Rubric.objects.create(name = 'cars')
        testuser = AdvUser.objects.create(is_activated = True, send_messages = True,
                               username = 'Alex', first_name = 'Alexander',
                               last_name = 'Smith', email = 'alex@gmail.com')
        testbb = Bb.objects.create(title = 'car', content='red', price = 20000,
                          contacts = 'Call', author = testuser, rubric = testrubric)
        AdditionalImage.objects.create(bb = testbb, image = '29.07.21')

    def test_bb_str(self):
        bb = Bb.objects.get(title='car')
        self.assertEqual(bb.__str__(), 'cars - car')

    def test_bb_delete(self):
        bb = Bb.objects.get(title='car')
        self.assertEqual(len(AdditionalImage.objects.all()), 1)
        bb.delete()
        self.assertEqual(len(AdditionalImage.objects.all()), 0)

    def test_bb_get_absolute_url(self):
        bb = Bb.objects.get(id=1)
        self.assertEqual(bb.get_absolute_url(), '1/1')