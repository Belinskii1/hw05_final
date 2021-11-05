from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.test import TestCase
import shutil
import tempfile
from django.conf import settings
from django.core.cache import cache

from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class CacheViwesTest(TestCase):
    ''' При удалении записи из базы, она остаётся в response.content главной
    страницы до тех пор, пока кэш не будет очищен принудительно.'''
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username='author_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост для проверки кеширования страницы',
            author=cls.author_user,
            group=cls.group)
 
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
 
    def setUp(self):
        self.guest_client = Client()
 
    def test_index_page_cache(self):
        created_post = Post.objects.filter(pk=CacheViwesTest.post.pk)
        # Проверка существования поста в базе данных
        self.assertTrue(created_post.exists(),
                        'Пост отстутствует в базе данных')
        # Проверка существования поста на стартовой странице
        response = self.guest_client.get(
            reverse('posts:posts'))
        self.assertIn(CacheViwesTest.post, response.context['page_obj'
                                                            ].object_list,
                      'Пост отсутствует на главной странице')
        # Контент стартовой страницы до удаления поста
        page_content = response.content
        # Удаление поста
        CacheViwesTest.post.delete()
        # Проверка существования поста в базе данных после удаления
        self.assertFalse(created_post.exists(),
                         'Пост не удален в базе данных')
        # Контент стартовой страницы после удаления поста
        page_content_after_delete = self.guest_client.get(
            reverse('posts:posts')).content
        # Сравнение контента страницы до и после удаления поста
        self.assertEqual(page_content, page_content_after_delete,
                         'Кеширование не работает')
        # Очистка кеша
        cache.clear()
        # Контент стартовой страницы после очистки кеша
        page_content_after_cache_clear = self.guest_client.get(
            reverse('posts:posts')).content
        # Сравнение контента страницы до и после удаления после очистки кэша
        self.assertNotEqual(page_content_after_delete,
                            page_content_after_cache_clear)