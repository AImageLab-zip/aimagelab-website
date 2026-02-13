# Main app models
from django.db import models
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField


class UserProfile(models.Model):
    """Extended user profile for team members"""
    
    ROLE_CHOICES = [
        # ('professor_special', 'Full Professor (University Dean)'),
        ('full_professor', 'Full Professor'),
        ('assoc_professor', 'Associate Professor'),
        ('researcher_tt', 'Researcher (RTT)'),
        ('researcher_a', 'Researcher (RTD-A)'),
        ('researcher_b', 'Researcher (RTD-B)'),
        ('postdoc', 'Postdoctoral Researcher'),
        ('research_fellow', 'Research Fellow'),
        ('collaborator', 'External Collaborator'),
        ('phd', 'PhD Student'),
        ('intern', 'Research Intern'),
        ('alumni', 'Alumni'),
        ('past_member', 'Past Member'),
        ('guest', 'Visitor Researcher'), # ?
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='phd')
    bio = models.TextField(blank=True, help_text="Short biography")
    website = models.URLField(blank=True, help_text="Personal website or homepage")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    display_order = models.IntegerField(default=0, help_text="Order in team listing (lower first)")
    is_visible = models.BooleanField(default=True, help_text="Show on People page")
    
    # Alumni-specific fields
    current_position = models.CharField(max_length=200, blank=True, help_text="Current position (for alumni)")
    
    # Additional info
    google_scholar = models.URLField(blank=True)
    github = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    phone_number = PhoneNumberField(
        blank=True,
        null=True,
        region='IT',
        help_text="Contact phone number (international format)"
    )
    # IRIS Integration fields
    codice_fiscale = models.CharField(
        max_length=16,
        blank=True,
        null=True,
        unique=True,
        verbose_name="Codice Fiscale",
        help_text="Italian fiscal code (primary IRIS identifier)"
    )
    iris_pid = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="IRIS PID",
        help_text="IRIS person identifier (e.g., rp00491) - cached from API"
    )
    iris_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="IRIS Internal ID",
        help_text="IRIS internal ID - cached from API"
    )
    iris_id_ab = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="IRIS ID AB",
        help_text="IRIS ID AB - cached from API"
    )
    id_iris = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Legacy IRIS ID",
        help_text="Legacy field for backward compatibility"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"
    
    def get_full_name(self):
        return self.user.get_full_name() or self.user.username


class PublicationIRIS(models.Model):
    """Publication imported from IRIS"""
    # Primary fields from IRIS GW REST API
    handle = models.CharField(max_length=200, unique=True, null=True, blank=True, verbose_name="Handle", help_text="Unique handle identifier from IRIS")
    id_iris = models.CharField(max_length=50, blank=True, null=True, verbose_name="IRIS Internal ID", help_text="Internal legacy ID")
    
    titolo = models.TextField(verbose_name="Title")
    anno = models.IntegerField(null=True, blank=True, verbose_name="Year")
    autori = models.TextField(blank=True, verbose_name="Authors")
    keywords = models.JSONField(blank=True, verbose_name="Keywords", help_text="List of keywords (from IRIS)", default=list)
    
    # Publication details
    tipo = models.CharField(max_length=200, blank=True, verbose_name="Type")
    rivista = models.CharField(max_length=500, blank=True, verbose_name="Journal/Conference")
    abstract = models.TextField(blank=True, verbose_name="Abstract")
    doi = models.CharField(max_length=200, blank=True, verbose_name="DOI")
    isbn = models.CharField(max_length=100, blank=True, verbose_name="ISBN")
    issn = models.CharField(max_length=100, blank=True, verbose_name="ISSN")
    
    # Additional metadata
    volume = models.CharField(max_length=50, blank=True, verbose_name="Volume")
    numero = models.CharField(max_length=50, blank=True, verbose_name="Number")
    pagine = models.CharField(max_length=100, blank=True, verbose_name="Pages")
    editore = models.CharField(max_length=300, blank=True, verbose_name="Publisher")
    luogo = models.CharField(max_length=200, blank=True, verbose_name="Place")
    
    # File attachment
    pdf = models.URLField(max_length=500, blank=True, verbose_name="PDF URL")
    allegati = models.IntegerField(default=0, verbose_name="Attachment Count")
    
    # Additional IRIS fields
    url = models.URLField(max_length=500, blank=True, verbose_name="URL")
    stato = models.CharField(max_length=100, blank=True, verbose_name="Status")
    tipologia = models.CharField(max_length=200, blank=True, verbose_name="Typology")
    
    # New fields from GW REST API
    language = models.CharField(max_length=10, blank=True, verbose_name="Language Code")
    citation = models.TextField(blank=True, verbose_name="Citation")
    fulltext_available = models.BooleanField(default=False, verbose_name="Fulltext Available")
    
    # Citation metrics
    scopus_citations = models.IntegerField(default=0, verbose_name="Scopus Citations")
    wos_citations = models.IntegerField(default=0, verbose_name="WOS Citations")
    
    # System fields
    hidden = models.BooleanField(default=False, verbose_name="Hidden")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Many-to-many relationship with UserProfile
    authors = models.ManyToManyField(
        UserProfile,
        through='UserProfilePublicationIRIS',
        related_name='publications'
    )
    
    class Meta:
        verbose_name = "IRIS Publication"
        verbose_name_plural = "IRIS Publications"
        ordering = ['-anno', 'titolo']
        indexes = [
            models.Index(fields=['anno']),
            models.Index(fields=['handle']),
            models.Index(fields=['id_iris']),
        ]
    
    def __str__(self):
        return f"{self.titolo[:100]} ({self.anno})"


class UserProfilePublicationIRIS(models.Model):
    """Link table between UserProfile and Publications with position info"""
    user_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='publication_links'
    )
    publication = models.ForeignKey(
        PublicationIRIS,
        on_delete=models.CASCADE,
        related_name='staff_links'
    )
    posizione = models.IntegerField(default=0, verbose_name="Author Position")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "UserProfile-Publication Link"
        verbose_name_plural = "UserProfile-Publication Links"
        unique_together = [['user_profile', 'publication']]
        ordering = ['publication__anno', 'posizione']
    
    def __str__(self):
        return f"{self.user_profile} - {self.publication.titolo[:50]}"


class IRISImportLog(models.Model):
    """Log for IRIS import operations"""
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    staff_processed = models.IntegerField(default=0)
    publications_created = models.IntegerField(default=0)
    publications_updated = models.IntegerField(default=0)
    links_created = models.IntegerField(default=0)
    
    error_message = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "IRIS Import Log"
        verbose_name_plural = "IRIS Import Logs"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Import {self.id} - {self.status} at {self.started_at}"


class Category(models.Model):
    """Blog post category model"""
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name


class Post(models.Model):
    """Blog post model"""
    
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    cover = models.ImageField(upload_to='blog_covers/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='blog_thumbnails/', blank=True, null=True, help_text="Cropped thumbnail for news listings (480x200)")
    slug = models.SlugField(unique=True)
    
    
    categories = models.ManyToManyField("Category", related_name="posts")
    
    #author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    event_date = models.DateTimeField(blank=True, null=True)
    is_published = models.BooleanField(default=True)
    is_pinned = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class Project(models.Model):
    """Research project model"""

    name = models.CharField(max_length=200)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='project_logos/', blank=True, null=True, help_text="Project logo or icon")
    website = models.URLField(blank=True, help_text="Project website or homepage URL")
    founding_by = models.CharField(max_length=200, blank=True)
    project_type = models.CharField(max_length=100, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date', 'name']

    def __str__(self):
        return f"{self.title} ({self.name})"

