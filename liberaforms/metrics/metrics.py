from prometheus_client import Gauge

Users   = Gauge("liberaforms_users_total", "Total users in tenant")
Forms   = Gauge("liberaforms_forms_total", "Total forms in tenant")
Answers = Gauge("liberaforms_answers_total", "Total answers in tenant")

AttachmentSize = Gauge("liberaforms_attachments_bytes_total",
                       "Total attachment size (bytes) in tenant")
MediaSize = Gauge("liberaforms_media_bytes_total",
                  "Total media size (bytes) in tenant")

def initialize_metrics(app):
    from liberaforms.models.form import Form
    from liberaforms.models.user import User
    from liberaforms.models.answer import Answer, AnswerAttachment
    from liberaforms.models.media import Media
    def wrap_context(call):
        def f():
            with app.app_context():
                return call()
        return f
    Forms.set_function(wrap_context(Form.count))
    Users.set_function(wrap_context(User.count))
    Answers.set_function(wrap_context(Answer.count))
    AttachmentSize.set_function(wrap_context(AnswerAttachment.calc_total_size))
    MediaSize.set_function(wrap_context(Media.calc_total_size))
