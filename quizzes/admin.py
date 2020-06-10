from django.contrib import admin
import nested_admin
from .models import Quiz, Category, Question, Answer, Feedback, UserResponse


class AnswerInline(nested_admin.NestedTabularInline):
    """
    This is the Answer input section that appears on the Quiz Admin page.

    When creating a new Quiz the nested_admin module
    allows for the Quiz, Category, Question, and Answer
    inputs to all appear on the same page.
    """
    model = Answer
    exclude = ['parent_quiz', 'parent_category', 'answer_selected']


class QuestionInline(nested_admin.NestedTabularInline):
    """
    This is the Question input section that appears on the Quiz Admin page.

    When creating a new Quiz the nested_admin module
    allows for the Quiz, Category, Question, and Answer
    inputs to all appear on the same page.
    """
    model = Question
    exclude = ['parent_quiz', 'parent_category']
    inlines = [AnswerInline,]


class CategoryInline(nested_admin.NestedTabularInline):
    """
    This is the Category input section that appears on the Quiz Admin page.

    When creating a new Quiz the nested_admin module
    allows for the Quiz, Category, Question, and Answer
    inputs to all appear on the same page.
    """
    model = Category
    exclude = ['order', 'score']
    inlines = [QuestionInline,]


class QuizAdmin(nested_admin.NestedModelAdmin):
    """
    This is the Quiz Admin view.

    When creating a new Quiz the nested_admin module
    allows for the Quiz, Category, Question, and Answer
    inputs to all appear on the same page.
    """
    inlines = [CategoryInline,]


class FeedbackInline(admin.TabularInline):
    model = Feedback
    inlines = [Feedback,]


class UserResponseAdmin(admin.ModelAdmin):
    list_display = ['response_id', 'parent_quiz']
    ordering = ['parent_quiz']
    model = UserResponse


admin.site.register(Quiz, QuizAdmin)
admin.site.register(Category)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Feedback)
admin.site.register(UserResponse, UserResponseAdmin)
