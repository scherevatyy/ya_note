from http import HTTPStatus
from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import WARNING


User = get_user_model()


class TestNoteCreate(TestCase):
    NOTE_TEXT = 'Текст заметки'
    NOTE_SLUG = 'slug'
    NOTE_TITLE = 'Title'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Username')
        cls.url = reverse('notes:add')
        cls.success_url = ('notes:success')
        cls.form_data = {
            'text': cls.NOTE_TEXT,
            'slug': cls.NOTE_SLUG,
            'title': cls.NOTE_TITLE,
            }

    def test_anonymous_user_cant_create_note(self):
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_auth_user_can_create_note(self):
        self.client.force_login(self.user)
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.slug, self.NOTE_SLUG)
        self.assertEqual(note.author, self.user)

    def test_not_unique_slug(self):
        self.client.force_login(self.user)
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        response = self.client.post(self.url, data=self.form_data)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=(self.NOTE_SLUG + WARNING)
        )
        self.assertEqual(notes_count, 1)

    def test_empty_slug(self):
        self.form_data.pop('slug')
        self.client.force_login(self.user)
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(note.slug, expected_slug)


class TestNoteEditDelete(TestCase):
    NOTE_TEXT = 'Текст заметки'
    NEW_NOTE_TEXT = 'Обновлённый текст заметки'
    NEW_NOTE_TITLE = 'Обновленный заголовок'
    SLUG = 'slug'

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('notes:detail', args=(cls.SLUG,))
        cls.edit_url = reverse('notes:edit', args=(cls.SLUG,))
        cls.delete_url = reverse('notes:delete', args=(cls.SLUG,))
        cls.success_url = reverse('notes:success')
        cls.author = User.objects.create(username='Автор заметки')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.another_user = User.objects.create(username='Пользователь')
        cls.another_client = Client()
        cls.another_client.force_login(cls.another_user)
        cls.note = Note.objects.create(title='Заголовок',
                                       text=cls.NOTE_TEXT,
                                       slug=cls.SLUG,
                                       author=cls.author)
        cls.form_data = {
            'text': cls.NEW_NOTE_TEXT,
            'title': cls.NEW_NOTE_TEXT,
            'slug': cls.SLUG,
            'author': cls.author,
            }

    def test_author_can_delete_note(self):
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.success_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        response = self.another_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)

    def test_user_cant_edit_note_of_another_user(self):
        response = self.another_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_TEXT)
