from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()

NOTES_AMOUNT_FOR_READER = 0


class TestNotesList(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Username')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.notes = Note.objects.create(
            title='Тестовая заметка',
            text='Просто текст.',
            author_id=cls.author.id,
        )

    def test_authorized_client_has_form(self):
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.notes.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name):
                self.client.force_login(self.author)
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIn('form', response.context)

    def test_notes_for_another_user(self):
        self.client.force_login(self.reader)
        url = reverse('notes:list')
        response = self.client.get(url)
        object_list = response.context['object_list']
        notes_count = len(object_list)
        self.assertEqual(notes_count, NOTES_AMOUNT_FOR_READER)

    def test_note_in_list_for_author(self):
        self.client.force_login(self.author)
        url = reverse('notes:list')
        response = self.client.get(url)
        object_list = response.context['object_list']
        self.assertIn(self.notes, object_list)
