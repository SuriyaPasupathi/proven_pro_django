# profile_fields.py

BASE_FIELDS = [
    'first_name', 'last_name', 'bio', 'profile_mail'
]

STANDARD_FIELDS = BASE_FIELDS + [
    'mobile', 'services_categories', 'services_description', 'rate_range', 'availability',
    'company_name', 'position', 'key_responsibilities', 'experience_start_date', 'experience_end_date',
    'primary_tools', 'technical_skills', 'soft_skills', 'skills_description'
]

PREMIUM_FIELDS = STANDARD_FIELDS + [
    'project_title', 'project_description', 'project_url',
    'certifications_name', 'certifications_issuer', 'certifications_issued_date',
    'certifications_expiration_date', 'certifications_id',
    'video_description'
]

SUBSCRIPTION_FIELDS = {
    'free': BASE_FIELDS,
    'standard': STANDARD_FIELDS,
    'premium': PREMIUM_FIELDS
}

FILE_FIELDS = {
    'profile_pic': 'profile_pic',
    'video_intro': 'video_intro',
    'project_image': 'project_image',
    'certifications_image': 'certifications_image'
}

URL_FIELDS = [
    'profile_pic_url', 'video_intro_url', 'project_image_url', 'certifications_image_url'
]
