from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = self.client

    def test_static_pages(self):
        templates = ('/', '/about/author/', '/about/tech/')
        for temp in templates:
            response = self.guest_client.get(temp)
            self.assertEqual(response.status_code, HTTPStatus.OK.value)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_name')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тест сам себя не протестит',
            slug='test_group'
        )
        cls.post = Post.objects.create(
            text='Test_text',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template_not_auth(self):
        """проверяем доступы к шаблонам не зарегистрированного пользователя"""
        cache.clear()
        templates_url_names = {
            'posts/index.html': reverse(
                'posts:posts'),
            'posts/group_list.html': reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': self.user}
            ),
            'posts/post_detail.html': reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_urls_users_post_create_auth(self):
        """проверяем доступы к созданию
         поста зарегистрированного пользователя"""
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_urls_users_post_edit_auth(self):
        """проверяем доступы к редактированию поста
        зарегистрированного пользователя автора поста"""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_unixating_page(self):
        """проверяем, что запрос к несуществующей
         странице вернёт ошибку 404"""
        response = self.client.get('/create/new/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND.value)

    def test_auth_user_can_comment_post(self):
        """проверяем доступы к комментированию
        зарегистрированного пользователя автора поста"""
        self.authorized_client.post(reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.id}),
            {'text': self.post.text}
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertTemplateUsed(
            response,
            'posts/post_detail.html'
        )
