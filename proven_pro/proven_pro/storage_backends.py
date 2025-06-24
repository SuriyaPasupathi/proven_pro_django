from storages.backends.s3boto3 import S3Boto3Storage

class MediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False


class ProfilePicStorage(S3Boto3Storage):
    location = 'media/profile_pics'
    file_overwrite = False

class VerificationDocStorage(S3Boto3Storage):
    location = 'media/verification_docs'
    file_overwrite = False

class VideoStorage(S3Boto3Storage):
    location = 'media/videos'
    file_overwrite = False

class CertificationStorage(S3Boto3Storage):
    location = 'media/certifications'
    file_overwrite = False

class ProjectImageStorage(S3Boto3Storage):
    location = 'media/project_images'
    file_overwrite = False 

