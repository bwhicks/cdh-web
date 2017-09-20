import datetime
import json

from attrdict import AttrDict, AttrMap
from bs4 import BeautifulSoup
import dateutil.parser
from django.contrib.sites.models import Site
from django.contrib.redirects.models import Redirect
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.text import slugify
from mezzanine.generic.models import AssignedKeyword, Keyword
from mezzanine.pages.models import Page, RichTextPage
from pucas.ldap import user_info_from_ldap, LDAPSearchException

from cdhweb.blog.models import BlogPost
from cdhweb.events.models import Event, Location, EventType
from cdhweb.people.models import Person, Profile, Title, Position
from cdhweb.projects.models import Project, ProjectResource, Grant, \
    Role, Membership, GrantType
from cdhweb.resources.models import ResourceType, LandingPage


class Command(BaseCommand):
    '''Parse JSON data exported from CDH Web v1.0 as generated by
    Django dumpdata and import content into cdhweb v2.0 models.'''
    help = __doc__

    displayable_fields = ('slug', '_meta_title', 'description',
        'gen_description', 'created', 'status', 'publish_date',
        'expiry_date', 'short_url', 'in_sitemap')

    def add_arguments(self, parser):
        parser.add_argument('input',
            help='Path to a JSON file created using dumpdata')
        parser.add_argument('--people', action='store_true',
            help='Import people only')
        parser.add_argument('--events', action='store_true',
            help='Import events only')
        parser.add_argument('--projects', action='store_true',
            help='Import projects only')
        parser.add_argument('--blog', action='store_true',
            help='Import blog posts only')
        parser.add_argument('--pages', action='store_true',
            help='Import content pages only')

    def handle(self, *args, **options):
        import_all = not any([options['people'], options['events'],
            options['projects'], options['blog'], options['pages']])

        try:
            with open(options['input'], 'r') as datafile:
                v1data = json.load(datafile)
        except OSError as err:
            raise CommandError(err)
        except json.decoder.JSONDecodeError as err:
            raise CommandError('Error parsing JSON: %s' %err)

        self.current_site = Site.objects.get_current()

        # TODO: summary. # created/update
        if import_all or options['people']:
            self.import_profiles(v1data)
        if import_all or options['events']:
            self.import_events(v1data)
        if import_all or options['projects']:
            self.import_projects(v1data)
        if import_all or options['blog']:
            self.import_blogposts(v1data)
        if import_all or options['pages']:
            self.import_pages(v1data)

    def import_profiles(self, data):
        # use current date for start date of positions created via import
        today = timezone.now()

        # create permanent redirect from old about/staff to new people/staff
        Redirect.objects.get_or_create(site=self.current_site,
            old_path='/about/staff/', new_path='/people/staff/')

        # track original staffer pk for associating staffer page content
        orig_pk = {}

        # loop through the data and process staffprofiles.staffer
        for item_data in data:
            item = AttrDict(item_data)
            if item.model == 'staffprofiles.staffer':
                try:
                    # get user by email if possible
                    user = Person.objects.get(email=item.fields.email)
                except ObjectDoesNotExist:
                    user = self.init_user(item.fields.email, item)

               # create profile if it does not yet exist
                try:
                    user.profile
                except ObjectDoesNotExist:
                    user.profile = Profile.objects.create(user=user)

                # store by pk to match up with staff page content
                orig_pk[item.pk] = user
                # convert education from plain text to html list
                education = ['<li>%s</li>' % line.strip() for line in item.fields.education.split(';')]
                user.profile.education = '<ul>\n%s\n</ul>' % '\n'.join(education)

                # all people in old site are cdh staff
                user.profile.is_staff = True
                # associate with current site
                user.profile.site = self.current_site
                user.profile.save()

                # TBD: is there any useful way to preserve existing photos?

                # map previous display title to current position
                # (skip if user already has a current title)
                if item.fields.title and not user.current_title:
                    jobtitle, created = Title.objects.get_or_create(title=item.fields.title)
                    Position.objects.create(user=user, title=jobtitle,
                        start_date=today)

                user.save()

        # next loop through the data and process staffprofiles.stafferpage
        for item_data in data:
            item = AttrDict(item_data)
            if item.model == 'staffprofiles.stafferpage':
                # get associated user based on v1 pk
                user = orig_pk[item.fields.staffer_data]
                user.profile.bio = item.fields.extra_content
                # displayable fields map unchanged
                for field in self.displayable_fields:
                    setattr(user.profile, field, item.fields[field])
                user.profile.save()


    # emails that do not correspond to netid
    email_aliases = {
        'rebecca.s.koeser': 'rkoeser',
        'nbenedict': 'nfrye'
    }

    def init_user(self, email, staffdata):
        '''Create new user and initialize from LDAP if possible; otherwise,
        initialize from import data'''
        netid = email.split('@')[0]
        # convert email to alias if necessary
        netid = self.email_aliases.get(netid, netid)

        # NOTE: using get or create for case where old email doesn't
        # match new email, but netid does
        user, created = Person.objects.get_or_create(username=netid)
        try:
            # initialize via pucas
            user_info_from_ldap(user)
        except LDAPSearchException:
            self.stderr.write('Error loading directory information for %s' % netid)
            # set basic info from staffdata
            user.email = staffdata.fields.email
            user.first_name, user.last_name = staffdata.fields.name.rsplit(' ', 1)
            user.save()
            profile = Profile.objects.create(user=user)
            profile.title = staffdata.fields.name
            profile.save()

        return user

    # known variants for CDH location
    cdh_locations = [
        "B Floor Firestone Library",
        "B Floor",
        "B Floor, Firestone Library",
        "B Floor, Firestone",
        "CDH",
        "Firestone Library, Floor B, Center for Digital Humanities",
    ]
    # "245 East Pyne"

    def import_events(self, data):
        # preload cdh location for associating with events
        cdh = Location.objects.get(short_name='CDH')
        event_type_lookup = {event.name: event for event in EventType.objects.all()}
        event_type_lookup['Lecture'] = event_type_lookup['Guest Lecture']

        # loop through the data and process eventspages.event
        for item_data in data:
            item = AttrDict(item_data)
            if item.model == 'eventspages.event':
                # preserve event pk since it is used in old urls
                try:
                    # get event if has already been created
                    event = Event.objects.get(pk=item.pk)
                except ObjectDoesNotExist:
                    event = Event(pk=item.pk)

                self.set_event_type(event, item, event_type_lookup)

                event.content = item.fields.event_description
                event.start_time = dateutil.parser.parse(item.fields.event_start_time)
                event.end_time = dateutil.parser.parse(item.fields.event_end_time)

                if item.fields.event_location in self.cdh_locations:
                    event.location = cdh
                else:
                    # associate location?
                    self.stderr.write('Not handling location %s for %s' % \
                        (item.fields.event_location, item.fields.event_title))

                # associate with current site
                event.site = self.current_site
                # event_sponsor unused
                event.save()
                # images will be handled manually

        for item_data in data:
            item = AttrDict(item_data)
            if item.model == 'eventspages.eventpage':
                # event_data is pk for foreignkey to eventspages.event
                event = Event.objects.get(pk=item.fields.event_data)
                # copy displayable fields unchanged
                for field in self.displayable_fields:
                    setattr(event, field, item.fields[field])
                event.save()

                # handle keywords
                self.import_keywords(event, item)

    def set_event_type(self, event, item, event_type_lookup):
        if ':' in item.fields.event_title:
            ev_type, title = item.fields.event_title.split(': ', 1)
            if ev_type in event_type_lookup:
                event.event_type = event_type_lookup[ev_type]
                event.title = title
                return

        # in every other case, new event title is full title
        event.title = item.fields.event_title
        # repeating events: title is the type (e.g. reading group)
        if item.fields.event_title in event_type_lookup:
            event.event_type = event_type_lookup[item.fields.event_title]
            return

        if 'Open House' in item.fields.event_title:
            event.event_type = event_type_lookup['Reception']
            return

        if 'Working Group' in item.fields.event_title:
            event.event_type = event_type_lookup['Working Group']
            return

        self.stderr.write("Could not determine event type for %s; setting as lecture" % \
            item.fields.event_title)
        event.event_type = event_type_lookup['Guest Lecture']

    def import_projects(self, data):
        # track original project pk for associating project page content
        proj_orig_pk = {}
        website_resource_type = ResourceType.objects.get(name='website')
        # for import purposes, all grants will be considered
        # current-year sponsored projects (manual cleanup required)
        sponsored_proj = GrantType.objects.get_or_create(grant_type='Sponsored Project')[0]
        grant_start = datetime.date(year=2016, month=9, day=1)
        grant_end = datetime.date(year=2017, month=9, day=30)

        # loop through the data and process projectpages.page
        for item_data in data:
            item = AttrDict(item_data)
            if item.model == 'projectpages.project':
                try:
                    # get event if has already been created
                    proj = Project.objects.get(title=item.fields.project_title)
                except ObjectDoesNotExist:
                    proj = Project(title=item.fields.project_title)

                proj.short_description = item.fields.project_subtitle or ''
                proj.long_description = item.fields.project_description
                if item.fields.project_summary:
                    # FIXME: why isn't this sticking?
                    proj.description = item.fields.project_summary
                    proj.gen_description = False

                # associate with current site
                proj.site = self.current_site
                proj.save()

                # store by original pk to match up with page content
                proj_orig_pk[item.pk] = proj

        # next loop through the data and process projectpages.projectpage
        for item_data in data:
            item = AttrMap(item_data)
            if item.model == 'projectpages.projectpage':
                # get associated proj based on v1 pk
                proj = proj_orig_pk[item.fields.project_data]

                # special case: two projects have a project website
                # in the slug field
                if item.fields['slug'].startswith('http:'):
                    # create as website link
                    ProjectResource.objects.create(project=proj,
                        resource_type=website_resource_type,
                        url=item.fields['slug'])

                # For historical reasons, slug should be regenerated
                # from project title for all projects
                item.fields['slug'] = slugify(proj.title)

                # displayable fields map unchanged
                for field in self.displayable_fields:
                    setattr(proj, field, item.fields[field])
                proj.save()

                # handle keywords
                self.import_keywords(proj, item)

        # handle project roles and members
        role_orig_pk = {}
        for item_data in data:
            item = AttrMap(item_data)
            if item.model == 'projectpages.projectrole':
                try:
                    # get role if it has already been created
                    role = Role.objects.get(title=item.fields.title)
                except ObjectDoesNotExist:
                    role = Role(title=item.fields.title)

                role.sort_order = item.fields.rank
                role.save()
                # store reference by original pk for member lookup
                role_orig_pk[item.pk] = role

        for item_data in data:
            item = AttrDict(item_data)
            if item.model == 'projectpages.projectmember':

                proj = proj_orig_pk[item.fields.project[0]]
                role = role_orig_pk[item.fields.project_role]
                user = self.get_user_for_project_member(item.fields.name)

                if user:
                    # if user has already been associated, skip
                    if user in proj.members.all():
                        next

                    if proj.grant_set.count():
                        grant = proj.grant_set.first()
                    else:
                        grant = Grant.objects.create(project=proj,
                            grant_type=sponsored_proj,
                            start_date=grant_start,
                            end_date=grant_end)

                    Membership.objects.get_or_create(project=proj, user=user,
                        grant=grant,
                        role=role_orig_pk[item.fields.project_role])

    def get_user_for_project_member(self, name):
        # NOTE: use createcasuser to create users manually before running import
        first_name, last_name = name.rsplit(' ', 1)
        user = Person.objects.filter(last_name=last_name)
        if user.count() == 1:
            return user.first()

        self.stderr.write('User %s not found; creating stub user record' % \
            name)
        user = Person.objects.create(last_name=last_name,
            first_name=first_name, username=''.join([last_name, first_name]),
            is_active=False)
        return user

    def import_blogposts(self, data):
        for item_data in data:
            item = AttrDict(item_data)
            if item.model == 'blog.blogpost':
                try:
                    # get post if it has already been created
                    post = BlogPost.objects.get(slug=item.fields.slug)
                except ObjectDoesNotExist:
                    post = BlogPost(slug=item.fields.slug)

                # associate with current site
                post.site = self.current_site
                # set blog post title & content
                post.title = item.fields.title
                post.content = item.fields.content

                # NOTE: not maintaining associated author; needs to be handled
                # manually after import

                # displayable fields map unchanged
                for field in self.displayable_fields:
                    setattr(post, field, item.fields[field])
                post.save()

                # handle keywords
                self.import_keywords(post, item)

    landing_pages = ['about', 'research', 'grants', 'resources', 'community']

    def import_pages(self, data):
        # loop through and store stocklandingpage content by pk
        orig_landingpages = {}
        for item_data in data:
            item = AttrDict(item_data)
            if item.model == 'stocktemplate.stocklandingpage':
                orig_landingpages[item.pk] = item.fields

        orig_pks = {}
        for item_data in data:
            item = AttrDict(item_data)
            if item.model == 'pages.page' and \
               item.fields.content_model == "stocklandingpage":

                # use slug to determine if page should be a landing page

                if item.fields.slug in self.landing_pages:
                    page_model = LandingPage
                else:
                    # otherwise, use generic rich text page
                    page_model = RichTextPage

                try:
                    # get page if it has already been created
                    page = page_model.objects.get(slug=item.fields.slug)
                except ObjectDoesNotExist:
                    page = page_model(slug=item.fields.slug)

                # store for parent handling
                orig_pks[item.pk] = page

                # grab content from stocklandingpage
                # (page/stocklandingpage pks match because of table inheritance)

                soup = BeautifulSoup(orig_landingpages[item.pk].content,
                    'html.parser')
                if page_model is LandingPage:
                    # convert first heading to tagline and remove from content
                    heading = soup.find('h3')
                    if heading:
                        page.tagline = heading.get_text()
                        heading.extract()

                page.content = soup.prettify()
                # displayable fields map unchanged
                for field in self.displayable_fields:
                    setattr(page, field, item.fields[field])
                # page fields
                # for field in ['_order', 'parent', 'in_menus']:
                # TODO: update parent pks
                for field in ['title', '_order', 'in_menus']:
                    setattr(page, field, item.fields[field])
                if item.fields.parent:
                    page.parent = orig_pks[item.fields.parent]
                page.save()

        # create placeholder pages
        placeholders = {
            'Staff': {'slug': 'people/staff', 'parent_slug': 'about'},
            'Updates': {},
            'Events': {},
            'Projects': {'parent_slug': 'research'}
        }
        for title, info in placeholders.items():
            # use configured slug or slugify the title
            slug = info.get('slug', slugify(title))
            try:
                page = Page.objects.get(slug=slug)
            except ObjectDoesNotExist:
                page = Page(slug=slug)

            page.title = title
            page.description = "[placeholder for dynamic page in menus]"
            if 'parent_slug' in info:
                try:
                    page.parent = Page.objects.get(slug=info['parent_slug'])
                except ObjectDoesNotExist:
                    self.stderr.write('Could not find %s parent page %s' % \
                        (page.title, info['parent_slug']))
            page.save()

            self.import_keywords(page, item)

    def import_keywords(self, content_object, item):
        # convert keyword string into assigned keyword fields
        for keywd in item.fields['keywords_string'].split(' '):
            keywd = keywd.strip()
            db_keyword = Keyword.objects.get_or_create(title=keywd,
                slug=slugify(keywd))[0]
            AssignedKeyword.objects.create(keyword_id=db_keyword.id,
                content_object=content_object)


