from prometheus_client import Counter, Gauge, Histogram, Summary

countUsers  =  Gauge("liberaforms_users_total", "Total users in tenant")
countForms  =  Gauge("liberaforms_forms_total", "Total forms in tenant")
countAnswers = Gauge("liberaforms_answers_total", "New answers in tenant")

def initialize_metrics():
    from liberaforms.models.form import Form
    from liberaforms.models.user import User
    from liberaforms.models.answer import Answer
    countForms.set(Form.count())
    countUsers.set(User.count())
    countAnswers.set(Answer.count())
