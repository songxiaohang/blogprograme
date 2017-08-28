from ..models import Post, Category, Tag
from django import template

from django.db.models.aggregates import Count


register = template.Library()

# 最新文章模板标签
@register.simple_tag
def get_recent_posts(num=5):
    return Post.objects.all()[:num]

# 归档模板标签
@register.simple_tag
def archives():
    return Post.objects.dates('created_time', 'month', order='DESC')

# 分类模板标签
@register.simple_tag
def get_categories():
    # Count 计算分类下的文章数，其接受的参数为需要计数的模型的名称。
    return Category.objects.annotate(num_posts=Count('post')).filter(num_posts__gt=0)

# 标签云
@register.simple_tag
def get_tags():
    return Tag.objects.annotate(num_posts=Count('post')).filter(num_posts__gt=0)
