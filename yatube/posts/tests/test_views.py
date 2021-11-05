from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from ..models import Group, Post, Comment
from django.core.cache import cache

User = get_user_model()


class PostViewsTests(TestCase):
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
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_views_post_templates(self):
        """ Задание 1: проверка namespace:name"""
        cache.clear()
        template_view_names = {
            'posts/index.html': reverse('posts:posts'),
            'posts/group_list.html': reverse(
                'posts:group_list',
                kwargs={'slug': 'test_group'}
            ),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': 'Test_name'}
            ),
            'posts/post_detail.html': reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            ),
            'posts/create_post.html': reverse('posts:post_create'),
        }
        for template, reverse_name in template_view_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_views_post_post_edit(self):
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.id}
        ))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_homepage_show_correct_context(self):
        cache.clear()
        """Задание 2: проверка контекста"""
        response = self.authorized_client.get(reverse('posts:posts'))
        first_object = response.context['post_list'][0]
        post_text = first_object.text
        self.assertEqual(post_text, self.post.text)
        self.assertContains(response, self.user)
        self.assertContains(response, self.group.id)
        self.assertContains(response, self.post.id)

    def test_group_list_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test_group'}
        ))
        self.assertEqual(response.context.get('group').title, self.group.title)
        self.assertEqual(response.context.get(
            'group').description, self.group.description
        )
        self.assertEqual(response.context.get('group').slug, self.group.slug)
        self.assertContains(response, self.user)
        self.assertContains(response, self.group.id)
        self.assertContains(response, self.post.id)

    def test_post_detail_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.context.get('post').id, self.post.id)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get(
            'post').author.username, 'Test_name'
        )
        self.assertContains(response, self.user)
        self.assertContains(response, self.group.id)
        self.assertContains(response, self.post.id)

    def test_profile_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': 'Test_name'}
        ))
        self.assertEqual(response.context.get('author').username, 'Test_name')
        self.assertContains(response, self.user)
        self.assertContains(response, self.group.id)
        self.assertContains(response, self.post.id)


class NewPostCaseTest(TestCase):
    """Задание 3: дополнительная проверка при создании поста"""
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="Test_name1"
        )
        self.client.force_login(self.user)
        self.post = Post.objects.create(text=("Test post"), author=self.user)

    def test_new_post_index(self):
        cache.clear()
        """новая запись появл. на index"""
        response = self.client.get("/")
        self.assertContains(response, self.post.text)

    def test_new_post_profile(self):
        """новая запись появляется на персональной (profile)"""
        response = self.client.get(reverse(
            'posts:profile',
            kwargs={'username': 'Test_name1'}
        ))
        self.assertContains(response, self.post.text)

    def test_new_post_view(self):
        """новая запись появляется на (post_detail)"""
        response = self.client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}
        ))
        self.assertContains(response, self.post.text)

    def test_new_comment_appears(self):
        """после успешной отправки комментарий
        появляется на странице поста"""
        self.client.post(reverse('posts:add_comment',
                                     kwargs={'post_id': self.post.id}),
                              {'text': self.post.text})
        response_get_post_with_comment = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertIn(self.post.text,
                      response_get_post_with_comment.content.decode())
        comment_obj = Comment.objects.filter(author=self.user,
                                             post=self.post.pk).count()
        self.assertEqual(comment_obj, 1)


class PaginatorViewsTest(TestCase):
    """проверка пагинатора"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        objs = [
            Post(
                author=cls.auth,
                text=f'Тестовый текст {i} поста',
                group=cls.group
            ) for i in range(1, 14)]
        Post.objects.bulk_create(objs)

    def test_home_paginator_page_one_shows_ten_records(self):
        cache.clear()
        response = self.client.get(reverse('posts:posts'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_home_paginator_page_two_shows_three_records(self):
        cache.clear()
        response = self.client.get(reverse('posts:posts') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_group_list_paginator_page_one_shows_ten_posts(self):
        response = self.client.get(reverse('posts:group_list',
                                           kwargs={'slug': 'test-slug'}))
        self.assertEqual(len(response.context['page_obj']), 10)
