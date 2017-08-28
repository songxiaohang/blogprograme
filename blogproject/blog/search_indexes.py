from haystack import indexes
from .models import Post


'''
django haystack 规定：要相对某个 app 下的数据进行全文检索，
要在该 app 下创建一个 search_indexes.py 文件，
然后创建一个 XXIndex 类并继承 SearchIndex 和 Indexable。
'''
class PostIndex(indexes.SearchIndex, indexes.Indexable):
    # SearchIndex 类一贯的命名：当字段设置了 document=True，此字段名为 text。
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return Post

    def index_queryset(self, using=None):
        return self.get_model().objects.all()







