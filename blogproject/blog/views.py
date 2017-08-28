from django.shortcuts import render, get_object_or_404
from .models import Post, Category, Tag
import markdown

from comments.forms import CommentForm
from django.views.generic import ListView, DetailView

from django.utils.text import slugify
from markdown.extensions.toc import TocExtension
from django.db.models import Q

# 基于类的通用视图
class IndexView(ListView):
    # 告诉 Django 获取数据库的模型是 Post。
    model = Post

    # 指定渲染的模板
    template_name = 'blog/index.html'

    # 将获得的模型数据列表保存到 post_list 里
    context_object_name = 'post_list'

    # 指定 paginate_by 属性后开启分页功能，其值代表每一页包含多少篇文章。
    paginate_by = 5

    def get_context_data(self, **kwargs):
        # 首先获得父类生成的传递给模板的字典。
        context = super().get_context_data(**kwargs)

        '''
        父类生成的字典中已有 paginator、page_obj、is_paginated 这三个模板变量，
        paginator 是 Paginator 的一个实例，page_obj 是 Page 的一个实例，
        '''
        paginator = context.get('paginator')
        page = context.get('page_obj')
        is_paginated = context.get('is_paginated')

        # 调用自己写的 pagination_data 方法获得显示分页导航条需要的数据。
        pagination_data = self.pagination_data(paginator, page, is_paginated)

        # 将分页导航条的模板变量更新到 context 中，注意 pagination_data 方法返回的也是一个字典。
        context.update(pagination_data)

        return context

    def pagination_data(self, paginator, page, is_paginated):
        if not is_paginated:
            # 如果没有分页，则无需显示分页导航条，不用任何分页导航条的数据，因此返回一个空的字典
            return {}

        # 当前页左边连续的页码号，初始值为空。
        left = []

        # 当前页右边连续的页码号，初始值为空。
        right = []

        # 标示第 1 页页码后是否需要显示省略号。
        left_has_more = False

        # 标示最后一页页码前是否需要显示省略号。
        right_has_more = False

        # 标示是否需要显示第 1 页的页码号。
        first = False

        # 标示是否需要显示最后一页的页码号。
        last = False

        # 获得用户当前请求的页码号
        page_number = page.number

        # 获得分页后的总页数。
        total_pages = paginator.num_pages

        # 获得整个分页页码列表。
        page_range = paginator.page_range

        if page_number == 1:
            '''
            如果用户请求的是第一页的数据，那么当前页左边的不需要数据，因此 left=[]（已默认为空）。
            此时只要获取当前页右边的连续页码号，
            比如分页页码列表是 [1, 2, 3, 4]，那么获取的就是 right = [2, 3]。
            '''
            right = page_range[page_number:page_number + 2]

            '''
            如果最右边的页码号比最后一页的页码号减去 1 还要小，
            说明最右边的页码号和最后一页的页码号之间还有其它页码，因此需要显示省略号，通过 right_has_more 来指示。
            '''
            if right[-1] < total_pages - 1:
                right_has_more = True

            '''
            如果最右边的页码号比最后一页的页码号小，说明当前页右边的连续页码号中不包含最后一页的页码,
            所以需要显示最后一页的页码号，通过 last 来指示。
            '''
            if right[-1] < total_pages:
                last = True

        elif page_number == total_pages:
            left = page_range[(page_number - 3) if (page_number - 3) > 0 else 0:page_number - 1]

            if left[0] > 2:
                left_has_more = True

            if left_has_more > 1:
                first = True

        else:
            '''
            用户请求的既不是最后一页，也不是第 1 页，则需要获取当前页左右两边的连续页码号，
            这里只获取了当前页码前后连续两个页码，你可以更改这个数字以获取更多页码。
            '''
            left = page_range[(page_number - 3) if (page_number - 3) > 0 else 0:page_number - 1]
            right = page_range[page_number:page_number + 2]

            # 是否需要显示最后一页和最后一页前的省略号。
            if right[-1] < total_pages - 1:
                right_has_more = True
            if right[-1] < total_pages:
                last = True

            # 是否需要显示第 1 页和第 1 页后的省略号。
            if left[0] > 2:
                left_has_more = True
            if left[0] > 1:
                first = True

        data = {
            'left':left,
            'right':right,
            'left_has_more': left_has_more,
            'right_has_more':right_has_more,
            'first':first,
            'last':last,
        }
        return data


def detail(request, pk):
    post = get_object_or_404(Post, pk=pk)

    # 阅读量+1
    post.increase_views()

    post.body = markdown.markdown(post.body,
                                  extensions=[
                                      'markdown.extensions.extra',
                                      'markdown.extensions.codehilite',
                                      'markdown.extensions.toc',
                                  ])
    # 记得在顶部导入 CommentForm
    form = CommentForm()
    # 获取这篇 post 下的全部评论
    comment_list = post.comment_set.all()

    # 将文章、表单、以及文章下的评论列表作为模板变量传给 detail.html 模板，以便渲染相应数据。
    context = {'post':post,
               'form':form,
               'comment_list':comment_list
               }
    return render(request, 'blog/detail.html', context=context)

class PostDetailView(DetailView):
    # 这些属性的含义和 ListView 是一样的。
    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'

    def get(self, request, *args, **kwargs):
        # 覆写 get 方法的目的是因为每当文章被访问一次，就得将文章阅读量 +1
        # get 方法返回的是一个 HttpResponse 实例。
        # 之所以需要先调用父类的 get 方法，是因为只有当 get 方法被调用后，
        # 才有 self.object 属性，其值为 Post 模型实例，即被访问的文章 post 。
        response = super(PostDetailView, self).get(request, *args, **kwargs)

        # 将文章阅读量+1。
        self.object.increase_views()

        # 视图必须返回一个 HttpResponse 对象。
        return response

    def get_object(self, queryset=None):
        # 覆写 get_object 方法的目的是因为需要对 post 的 body 值进行渲染。
        post = super(PostDetailView, self).get_object(queryset=None)
        md = markdown.Markdown(extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.codehilite', # 代码高亮
            #'markdown.extensions.toc', # 自动生成目录的拓展
            TocExtension(slugify=slugify),
        ])
        post.body = md.convert(post.body)
        post.toc = md.toc
        return post

    def get_context_data(self, **kwargs):
        # 覆写 get_context_data 的目的是因为除了将 post 传递给模板外，
        # 还要把评论表单，post下的评论列表传递给模板。
        context = super(PostDetailView, self).get_context_data(**kwargs)
        form = CommentForm()
        comment_list = self.object.comment_set.all()
        context.update({
            'form':form,
            'comment_list':comment_list
        })
        return context


def archives(request, year, month):
    post_list = Post.objects.filter(created_time__year=year,
                                    created_time__month=month
                                    )
    return render(request, 'blog/index.html', context={'post_list':post_list})

class ArchivesView(IndexView):
    def get_queryset(self):
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        return super(ArchivesView, self).get_queryset().filter(created_time__year=year,
                                                               created_time__month=month)


class CategoryView(IndexView):
    def get_queryset(self):
        cate = get_object_or_404(Category, pk=self.kwargs.get('pk'))
        return super(CategoryView, self).get_queryset().filter(category=cate)


class TagView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'

    def get_queryset(self):
        tag = get_object_or_404(Tag, pk=self.kwargs.get('pk'))
        return super(TagView, self).get_queryset().filter(tags=tag)


def search(request):
    # 获取用户提交的搜索关键词，GET 是类似于字典的对象，所以我们取的是值，
    # 'q' 是因为表单中搜索框input的name属性的值为 q 。
    q = request.GET.get('q')
    error_msg = ''

    # 如果没有输入关键词。
    if not q:
        error_msg = '请输入关键字'
        return render(request, 'blog/index.html', {'error_msg':error_msg})

    # 如果用户输入关键词。
    # 过滤条件contains是包含关键词，前缀i表示不区分大小写。
    # Q对象用于包装查询表达式，作用是提供复杂的查询逻辑。
    post_list = Post.objects.filter(Q(title__icontains=q) | Q(body__icontains=q))
    return render(request, 'blog/index.html', {'error_msg':error_msg,
                                               'post_list':post_list})
def contact(request):
    return render(request, 'blog/contact.html')

def about(request):
    return render(request, 'blog/about.html')
