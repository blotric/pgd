from django.db import models
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index


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
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
        ImageChooserPanel('header_image'),
    ]

    # Parent page / subpage type rules

    parent_page_types = ['home.HomePage', 'pgd.ContentPage']
    subpage_types = ['pgd.ContentPage']

    class Meta:
        verbose_name = 'content page'
        verbose_name_plural = 'content pages'