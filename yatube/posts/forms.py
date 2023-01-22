from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('text', 'group', 'image',)
        help_text = {
            'text': 'Текст поста',
            'group': 'Группа',
            'image': 'Картинка',
        }

    def clean_text(self):
        data = self.cleaned_data['text']

        if not data:
            raise forms.ValidationError('Заполните поле текст!')

        return data


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
        help_text = {'text': 'Прокомментируйте сей шедевр'}

    def clean_text(self):
        data = self.cleaned_data['text']

        if not data:
            raise forms.ValidationError('Заполните поле текст!')

        return data
