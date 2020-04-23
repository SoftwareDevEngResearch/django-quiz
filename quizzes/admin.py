from django.contrib import admin
import nested_admin
from .models import Quiz, Category, Question, Answer, Feedback


class AnswerInline(nested_admin.NestedTabularInline):
    model = Answer
    exclude = ['parent_quiz', 'parent_category', 'answer_selected']


class QuestionInline(nested_admin.NestedTabularInline):
    model = Question
    exclude = ['parent_quiz', 'parent_category']
    inlines = [AnswerInline,]


class CategoryInline(nested_admin.NestedTabularInline):
    model = Category
    exclude = ['order', 'score']
    inlines = [QuestionInline,]


class QuizAdmin(nested_admin.NestedModelAdmin):
    inlines = [CategoryInline,]

class FeedbackInline(admin.TabularInline):
    model = Feedback
    inlines = [Feedback,]


admin.site.register(Quiz, QuizAdmin)
admin.site.register(Category)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Feedback)
