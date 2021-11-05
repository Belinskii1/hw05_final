from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from ..models import Post, Follow


User = get_user_model()


class CommentTest(TestCase):

    def setUp(self):
        self.client_auth = Client()
        self.user1 = User.objects.create_user(username="sarah")
        self.user2 = User.objects.create_user(username="james")
        self.client_auth.force_login(self.user1)

        self.client_unauth = Client()

    def test_auth_user_can_subscribe(self):
        response = self.client_auth.get(
            reverse('posts:profile', kwargs={'username': self.user2}))
        self.assertIn("Подписаться", response.content.decode())
        self.assertNotIn("Отписаться", response.content.decode())

        response_subscribe = self.client_auth.post(reverse('posts:profile_follow',
                                                           kwargs={'username': self.user2}),
                                                   follow=True)
        is_follow = Follow.objects.filter(user=self.user1,
                                          author=self.user2).count()
        self.assertEqual(is_follow, 1)
        self.assertIn("Отписаться", response_subscribe.content.decode())
    
    def test_auth_user_can_unsubscribe(self):
        Follow.objects.create(user=self.user1, author=self.user2)
        is_follow = Follow.objects.filter(user=self.user1,
                                          author=self.user2).count()
        self.assertEqual(is_follow, 1)
        response_unsubscribe = self.client_auth.post(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.user2}), follow=True)
        self.assertIn("Подписаться", response_unsubscribe.content.decode())

        follow_obj = Follow.objects.filter(user=self.user1,
                                           author=self.user2).count()
        self.assertEqual(follow_obj, 0)

    def test_new_post_appears_in_follow_index(self):
        self.post_user2 = Post.objects.create(
            text='simple text post favorite author',
            author=self.user2
        )
        self.follow = Follow.objects.create(
            user=self.user1, author=self.user2
        )
        follow_index_page = self.client_auth.get(reverse(
            'posts:follow_index'))
        self.assertIn("simple text post favorite author",
                      follow_index_page.content.decode())

    def test_not_follow_post_dont_appears_in_follow_index(self):
        self.post_user2 = Post.objects.create(
            text='simple text post favorite author',
            author=self.user2
        )
        follow_index_page = self.client_auth.get(reverse(
            'posts:follow_index'))
        self.assertNotIn("simple text post favorite author",
                         follow_index_page.content.decode())
