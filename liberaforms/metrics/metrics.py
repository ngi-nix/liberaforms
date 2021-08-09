from prometheus_client import Counter, Gauge, Histogram, Summary

countUsers   = Gauge("liberaforms_users_total", "Total users in tenant")
countForms   = Gauge("liberaforms_forms_total", "Total forms in tenant")
countAnswers = Gauge("liberaforms_answers_total", "Total answers in tenant")

countAnswerAttachmentSize = Gauge("liberaforms_attachments_bytes_total",
                                  "Total attachment size (bytes) in tenant")
countMediaSize = Gauge("liberaforms_media_bytes_total",
                       "Total media size (bytes) in tenant")

def initialize_metrics():
    from liberaforms.models.form import Form
    from liberaforms.models.user import User
    from liberaforms.models.answer import Answer, AnswerAttachment
    from liberaforms.models.media import Media
    countForms.set(Form.count())
    countUsers.set(User.count())
    countAnswers.set(Answer.count())
    countAnswerAttachmentSize.set(AnswerAttachment.calc_total_size())
    countMediaSize.set(Media.calc_total_size())
