from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.notes = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author_id=cls.author.id
        )

    def test_pages_availability_for_anonymous_user(self):
        urls = (
            'notes:home',
            'users:login',
            'users:logout',
            'users:signup',
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_edit_delete_and_detail(self):
        users_statuses = (
            (self.author, HTTPStatus.OK, 'notes:edit'),
            (self.reader, HTTPStatus.NOT_FOUND, 'notes:edit'),
            (self.author, HTTPStatus.OK, 'notes:delete'),
            (self.reader, HTTPStatus.NOT_FOUND, 'notes:delete'),
            (self.author, HTTPStatus.OK, 'notes:detail'),
            (self.reader, HTTPStatus.NOT_FOUND, 'notes:detail'),
        )
        for user, status, link in users_statuses:
            self.client.force_login(user)
            with self.subTest(user=user, link=link):
                url = reverse(link, args=(self.notes.slug,))
                response = self.client.get(url)
                self.assertEqual(response.status_code, status)

    def test_availability_for_list_add_and_done(self):
        urls = (
            'notes:list',
            'notes:add',
            'notes:success',
        )
        self.client.force_login(self.author)
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_anonymous_client(self):
        login_url = reverse('users:login')
        urls = (
            ('notes:edit', (self.notes.slug,)),
            ('notes:delete', (self.notes.slug,)),
            ('notes:list', None),
            ('notes:detail', (self.notes.slug,)),
            ('notes:success', None),
            ('notes:add', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
