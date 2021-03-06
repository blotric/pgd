from django.db import models

from wagtail.core.models import Page, Orderable
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel
from wagtail.images.edit_handlers import ImageChooserPanel

from modelcluster.fields import ParentalKey, ParentalManyToManyField


class HomePage(Page):
    content_panels = Page.content_panels + [
        InlinePanel('gallery_images', label="Gallery images"),
        InlinePanel('related_blog_posts', label="News"),
    ]


class HomePageGalleryImage(Orderable):
    page = ParentalKey(HomePage, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+'
    )
    caption = models.CharField(blank=True, max_length=250)

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('caption'),
    ]


class RelatedBlogPage(Orderable):
    post = ParentalKey('HomePage', on_delete=models.CASCADE, related_name='related_blog_posts')
    news_article = models.ForeignKey('pgd.PostPage', on_delete=models.CASCADE, related_name="+")
    panels = [
        FieldPanel('news_article')
    ]