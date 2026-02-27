from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import ForumPost, ForumAnswer


class BlogForumViewTests(TestCase):
    def setUp(self):
        self.url = reverse('core:blog_forum')
        self.user = User.objects.create_user(
            username='forumtester',
            email='forumtester@example.com',
            password='StrongPass123!'
        )

    def test_forum_page_loads(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/blog_forum.html')

    def test_unauthenticated_user_cannot_post_question(self):
        response = self.client.post(self.url, {
            'title': 'How do I schedule emails?',
            'content': 'I need help setting this up.'
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('account_login'))
        self.assertEqual(ForumPost.objects.count(), 0)

    def test_authenticated_user_can_post_question(self):
        self.client.login(username='forumtester', password='StrongPass123!')

        response = self.client.post(self.url, {
            'title': 'How do I import subscribers?',
            'content': 'CSV import fails on row 25.'
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)
        self.assertEqual(ForumPost.objects.count(), 1)

        question = ForumPost.objects.first()
        self.assertEqual(question.title, 'How do I import subscribers?')
        self.assertEqual(question.content, 'CSV import fails on row 25.')
        self.assertEqual(question.user, self.user)

    def test_forum_posts_paginate(self):
        for idx in range(11):
            ForumPost.objects.create(
                user=self.user,
                title=f'Question {idx}',
                content=f'Content for question {idx}'
            )

        response_page_1 = self.client.get(self.url)
        response_page_2 = self.client.get(self.url, {'page': 2})

        self.assertEqual(response_page_1.status_code, 200)
        self.assertEqual(response_page_2.status_code, 200)
        self.assertEqual(len(response_page_1.context['forum_posts']), 10)
        self.assertEqual(len(response_page_2.context['forum_posts']), 1)

    def test_authenticated_user_can_post_answer(self):
        question = ForumPost.objects.create(
            user=self.user,
            title='How do I warm up a sender domain?',
            content='Need best practices for first week.'
        )
        helper = User.objects.create_user(
            username='helper',
            email='helper@example.com',
            password='StrongPass456!'
        )
        self.client.login(username='helper', password='StrongPass456!')

        response = self.client.post(self.url, {
            'post_type': 'answer',
            'question_id': str(question.id),
            'content': 'Start with low volume and gradually increase over 2-3 weeks.'
        })

        self.assertEqual(response.status_code, 302)
        self.assertIn(f'#question-{question.id}', response.url)
        self.assertEqual(ForumAnswer.objects.count(), 1)

        answer = ForumAnswer.objects.first()
        self.assertEqual(answer.question, question)
        self.assertEqual(answer.user, helper)

    def test_unauthenticated_user_cannot_post_answer(self):
        question = ForumPost.objects.create(
            user=self.user,
            title='How do I set up SPF?',
            content='Need DNS record format.'
        )

        response = self.client.post(self.url, {
            'post_type': 'answer',
            'question_id': str(question.id),
            'content': 'Use a TXT record with include and all directive.'
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('account_login'))
        self.assertEqual(ForumAnswer.objects.count(), 0)
