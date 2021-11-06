import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class CacheViwesTest(TestCase):
    """При удалении записи из базы, она остаётся в response.content главной
    страницы до тех пор, пока кэш не будет очищен"""
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
        self.assertTrue(created_post.exists(),
                        'Пост отстутствует в базе данных')
        response = self.guest_client.get(
            reverse('posts:posts'))
        self.assertIn(CacheViwesTest.post, response.context['page_obj'
                                                            ].object_list,
                      'Пост отсутствует на главной странице')
        page_content = response.content
        CacheViwesTest.post.delete()
        self.assertFalse(created_post.exists(),
                         'Пост не удален в базе данных')
        page_content_after_delete = self.guest_client.get(
            reverse('posts:posts')).content
        self.assertEqual(page_content, page_content_after_delete,
                         'Кеширование не работает')
        cache.clear()
        page_content_after_cache_clear = self.guest_client.get(
            reverse('posts:posts')).content
        self.assertNotEqual(page_content_after_delete,
                            page_content_after_cache_clear)
