import shutil
import tempfile

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test_name')
        cls.group = Group.objects.create(
            title='Test group',
            description='Test description',
            slug='test_group'
        )
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post_form(self):
        """1.при отправке валидной формы создаётся новая запись в бд"""
        posts_count = Post.objects.count()
        form_data = {
            'text': self.post.text
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        last_post = Post.objects.order_by('-id')[0]
        self.assertEqual(form_data['text'], last_post.text)
        self.assertEqual(last_post.id, self.post.id + 1)
        self.assertEqual(last_post.author, self.post.author)

    def test_create_post_with_group_form(self):
        """1.1 при отправке валидной формы
        создаётся новая запись в бд + группа"""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': self.post.text,
            'group': self.group.id,
            'image': uploaded
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        last_post = Post.objects.order_by('-id')[0]
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(form_data['text'], last_post.text)
        self.assertEqual(last_post.id, self.post.id + 1)
        self.assertEqual(form_data['group'], last_post.group.id)
        self.assertEqual(last_post.author, self.post.author)
        self.assertEqual(last_post.image, 'posts/small.gif')

    def test_post_edit_form(self):
        """2 происходит изменение поста post_id в базе данных."""
        form_data = {
            'text': self.post.text,
            'group': self.group.id
        }
        self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={
                    'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.post.refresh_from_db()
        self.assertEqual(Post.objects.get(
            id=self.post.id).text,
            form_data['text']
        )
        self.assertEqual(Post.objects.get(
            id=self.post.id).group.id,
            form_data['group']
        )

    def test_create_comment_form(self):
        """при отправке валидной формы создается новый комментарий"""
        form_data = {
            'text': 'comment text'
        }
        self.authorized_client.post(reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.id}),
            form_data
        )
        comment_obj = Comment.objects.filter(author=self.user,
                                             post=self.post.pk).count()
        self.assertEqual(comment_obj, 1)
        self.assertEqual(Comment.objects.get(
            author=self.user,
            post=self.post.pk).text,
            form_data['text']
        )
