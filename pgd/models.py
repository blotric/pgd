import datetime
from datetime import date

from django import forms
from django.db import models
from django.db.models import Q
from django.utils.dateformat import DateFormat
from django.utils.formats import date_format
from django.http import Http404, HttpResponse

from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, MultiFieldPanel, RichTextFieldPanel
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page, Orderable
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.snippets.models import register_snippet

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.tags import ClusterTaggableManager

from taggit.models import TaggedItemBase, Tag as TaggitTag


class ContentPage(Page):
    # Database fields

    body = RichTextField()
    publication_date = models.DateTimeField("Publication date")
    header_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    # Search index configuration

    search_fields = Page.search_fields + [
        index.SearchField('body'),
        index.FilterField('publication_date'),
    ]

    # Editor panels configuration

    content_panels = Page.content_panels + [
        FieldPanel('publication_date'),
        FieldPanel('body', classname="full"),
        InlinePanel('content_page_gallery_images', label="Gallery"),
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
        ImageChooserPanel('header_image'),
    ]

    # Parent page / subpage type rules

    parent_page_types = ['home.HomePage', 'pgd.ContentPage']
    subpage_types = ['pgd.ContentPage']

    show_in_menus_default = True

    class Meta:
        verbose_name = 'content page'
        verbose_name_plural = 'content pages'


class BlogPage(RoutablePageMixin, Page):
    description = models.CharField(max_length=255, blank=True,)

    content_panels = Page.content_panels + [
        FieldPanel('description', classname="full")
    ]

    def get_context(self, request, *args, **kwargs):
        context = super(BlogPage, self).get_context(request, *args, **kwargs)
        context['posts'] = self.posts
        context['blog_page'] = self
        context['search_type'] = getattr(self, 'search_type', "")
        context['search_term'] = getattr(self, 'search_term', "")
        return context

    def get_posts(self):
        return PostPage.objects.descendant_of(self).live().order_by('-date')

    @route(r'^(\d{4})/$')
    @route(r'^(\d{4})/(\d{2})/$')
    @route(r'^(\d{4})/(\d{2})/(\d{2})/$')
    def post_by_date(self, request, year, month=None, day=None, *args, **kwargs):
        self.posts = self.get_posts().filter(date__year=year)
        self.search_type = 'date'
        self.search_term = year
        if month:
            self.posts = self.posts.filter(date__month=month)
            df = DateFormat(date(int(year), int(month), 1))
            self.search_term = df.format('F Y')
        if day:
            self.posts = self.posts.filter(date__day=day)
            self.search_term = date_format(date(int(year), int(month), int(day)))
        return Page.serve(self, request, *args, **kwargs)

    @route(r'^(\d{4})/(\d{2})/(\d{2})/(.+)/$')
    def post_by_date_slug(self, request, year, month, day, slug, *args, **kwargs):
        post_page = self.get_posts().filter(slug=slug).first()
        if not post_page:
            raise Http404
        return Page.serve(post_page, request, *args, **kwargs)

    @route(r'^tag/(?P<tag>[-\w]+)/$')
    def post_by_tag(self, request, tag, *args, **kwargs):
        self.search_type = 'tag'
        self.search_term = tag
        self.posts = self.get_posts().filter(tags__slug=tag)
        return Page.serve(self, request, *args, **kwargs)

    @route(r'^category/(?P<category>[-\w]+)/$')
    def post_by_category(self, request, category, *args, **kwargs):
        self.search_type = 'category'
        self.search_term = category
        self.posts = self.get_posts().filter(categories__slug=category)
        return Page.serve(self, request, *args, **kwargs)

    @route(r'^$')
    def post_list(self, request, *args, **kwargs):
        self.posts = self.get_posts()
        return Page.serve(self, request, *args, **kwargs)

    @route(r'^search/$')
    def post_search(self, request, *args, **kwargs):
        search_query = request.GET.get('q', None)
        self.posts = self.get_posts()
        if search_query:
            self.posts = self.posts.filter(Q(body__contains=search_query)
                                           | Q(excerpt__contains=search_query)
                                           | Q(title__contains=search_query))
            self.search_term = search_query
            self.search_type = 'search'
        return Page.serve(self, request, *args, **kwargs)

    show_in_menus_default = True

    class Meta:
        verbose_name = "Article category"
        verbose_name_plural = "Article categories"


class PostPage(Page):
    body = RichTextField()
    date = models.DateTimeField(verbose_name="Post date", default=datetime.datetime.today)
    excerpt = RichTextField(
        verbose_name='excerpt', blank=True,
    )

    header_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    categories = ParentalManyToManyField('pgd.BlogCategory', blank=True)
    tags = ClusterTaggableManager(through='pgd.BlogPageTag', blank=True)

    content_panels = Page.content_panels + [
        ImageChooserPanel('header_image'),
        RichTextFieldPanel("body"),
        RichTextFieldPanel("excerpt"),
        FieldPanel('categories', widget=forms.CheckboxSelectMultiple),
        FieldPanel('tags'),
        InlinePanel('post_gallery_images', label="Gallery"),
    ]

    settings_panels = Page.settings_panels + [
        FieldPanel('date'),
    ]

    @property
    def blog_page(self):
        return self.get_parent().specific

    def get_context(self, request, *args, **kwargs):
        context = super(PostPage, self).get_context(request, *args, **kwargs)
        context['blog_page'] = self.blog_page
        context['blog_latest_posts'] = PostPage.objects.descendant_of(self.get_parent().specific).live().order_by('-date')
        context['post'] = self
        return context

    show_in_menus_default = True

    class Meta:
        verbose_name = "article"
        verbose_name_plural = "articles"


@register_snippet
class BlogCategory(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=80)

    panels = [
        FieldPanel('name'),
        FieldPanel('slug'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"


class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey('PostPage', related_name='post_tags')


class GalleryImage(Orderable):
    blog_post = ParentalKey(PostPage, on_delete=models.CASCADE, related_name='post_gallery_images',
                            null=True, blank=True)
    content_page = ParentalKey(ContentPage, on_delete=models.CASCADE, related_name='content_page_gallery_images',
                               null=True, blank=True)
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+'
    )
    caption = models.CharField(blank=True, max_length=250)

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('caption'),
    ]


@register_snippet
class Tag(TaggitTag):
    class Meta:
        proxy = True
