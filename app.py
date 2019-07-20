# @Time    : 2019/6/24 18:29
# @Author  : Jerry
# -*- coding:utf-8 -*-
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField,  PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import DeclarativeMeta
import requests
import json
import datetime
import jieba
import numpy as np
import config

app = Flask(__name__)
# 配置运行密钥
app.config["SECRET_KEY"] = '123456'
# 配置数据库地址
app.config.from_object(config)
# 跟踪数据库的修改，不用开启
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)

UserXm = ""
UserType = ""
UserUnit = ""
class LoginForm(FlaskForm):
    username = StringField('学工账号', validators=[DataRequired(message="账号不能为空"),
                                               Length(min=10,max=12,message="账号长度在10到12之间")])
    password = PasswordField('密码', validators=[DataRequired(message="密码不能为空")])
    submit = SubmitField('登陆')

class DxcOffices(db.Model):
    # 定义表名
    __tablename__ = 'dxcoffices'
    # db.Column定义字段
    id = db.Column(db.Integer(), primary_key=True)
    officeName = db.Column(db.String(50), unique=True, nullable=False)
    officePosition = db.Column(db.String(50), nullable=True)
    officeTeacher = db.Column(db.String(50), nullable=True, unique=False)
    officeNumber = db.Column(db.String(50), nullable=True, unique=False)
    # 方法显示一个可读字符串
    def __repr__(self):
        return '<dxcoffices: %s>' % self.officeName

class SpOffices(db.Model):
    __tablename__ = 'spoffices'
    id = db.Column(db.Integer(), primary_key=True)
    officeName = db.Column(db.String(50), unique=True, nullable=False)
    officePosition = db.Column(db.String(50), nullable=True)
    officeTeacher = db.Column(db.String(50), nullable=True, unique=False)
    officeNumber = db.Column(db.String(50), nullable=True, unique=False)
    def __repr__(self):
        return '<spoffices: %s>' % self.officeName

class NhOffices(db.Model):
    __tablename__ = 'nhoffices'
    id = db.Column(db.Integer(), primary_key=True)
    officeName = db.Column(db.String(50), unique=True, nullable=False)
    officePosition = db.Column(db.String(50), nullable=True)
    officeTeacher = db.Column(db.String(50), nullable=True, unique=False)
    officeNumber = db.Column(db.String(50), nullable=True, unique=False)
    def __repr__(self):
        return '<nhoffices: %s>' % self.officeName

class Faq(db.Model):
    __tablename__ = 'faq'
    id = db.Column(db.Integer(), primary_key=True)
    question = db.Column(db.String(200), unique=True, nullable=True)
    answer = db.Column(db.String(500), nullable=True)
    def __repr__(self):
        return '<faq: %s>' % self.question

class DxcAsso(db.Model):
    __tablename__ = 'dxcasso'
    type = db.Column(db.String(20))
    name = db.Column(db.String(50), primary_key=True)
    introduction = db.Column(db.String(500))
    activities = db.Column(db.String(100))
    def __repr__(self):
        return '<dxcasso: %s>' % self.name

class SpAsso(db.Model):
    __tablename__ = 'spasso'
    type = db.Column(db.String(20))
    name = db.Column(db.String(50), primary_key=True)
    introduction = db.Column(db.String(500))
    activities = db.Column(db.String(100))
    def __repr__(self):
        return '<spasso: %s>' % self.name

class NhAsso(db.Model):
    __tablename__ = 'nhasso'
    type = db.Column(db.String(20))
    name = db.Column(db.String(50), primary_key=True)
    introduction = db.Column(db.String(500))
    activities = db.Column(db.String(100))
    def __repr__(self):
        return '<nhasso: %s>' % self.name

class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data)  # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:  # 添加了对datetime的处理
                    if isinstance(data, datetime.datetime):
                        fields[field] = data.isoformat()
                    elif isinstance(data, datetime.date):
                        fields[field] = data.isoformat()
                    elif isinstance(data, datetime.timedelta):
                        fields[field] = (datetime.datetime.min + data).time().isoformat()
                    else:
                        fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)

def get_word_vector(s1,s2):
    """
    :param s1: 句子1
    :param s2: 句子2
    :return: 返回句子的余弦相似度
    """
    # 分词
    cut1 = jieba.cut(s1)
    cut2 = jieba.cut(s2)
    list_word1 = (','.join(cut1)).split(',')
    list_word2 = (','.join(cut2)).split(',')

    # 列出所有的词,取并集
    key_word = list(set(list_word1 + list_word2))
    # 给定形状和类型的用0填充的矩阵存储向量
    word_vector1 = np.zeros(len(key_word))
    word_vector2 = np.zeros(len(key_word))

    # 计算词频
    # 依次确定向量的每个位置的值
    for i in range(len(key_word)):
        # 遍历key_word中每个词在句子中的出现次数
        for j in range(len(list_word1)):
            if key_word[i] == list_word1[j]:
                word_vector1[i] += 1
        for k in range(len(list_word2)):
            if key_word[i] == list_word2[k]:
                word_vector2[i] += 1

    # 输出向量
    # print(word_vector1)
    # print(word_vector2)
    return word_vector1, word_vector2

def cos_dist(vec1,vec2):
    """
    :param vec1: 向量1
    :param vec2: 向量2
    :return: 返回两个向量的余弦相似度
    """
    dist1=float(np.dot(vec1,vec2)/(np.linalg.norm(vec1)*np.linalg.norm(vec2)))
    return dist1

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()

    url1 = "https://ssp.scnu.edu.cn/api/UserValidate.ashx"
    url2 = "https://ssp.scnu.edu.cn/api/GetUserinf.ashx"

    if request.method == 'POST':
        if form.validate_on_submit():  # 数据正确 并且验证csrf通过
            username = request.form.get('username')
            password = request.form.get('password')
            para = {"SchoolNum":"10574", "UserName":username, "PassWord":password}
            json_para = json.dumps(para)
            post_requst = requests.post(url1, data=json_para)
            post_request_json = json.loads(post_requst.text)
            status = post_request_json['Status']
            if status:
                '''
                获取登陆接口后的cookie，访问下一个接口获取信息requests库的session对象能够帮助
                我们跨请求保持某些参数，也会在同一个session实例发出的所有请求之间保持cookies
                '''
                sess = requests.session()
                cookie = post_requst.cookies
                get_request = sess.get(url2, cookies=cookie)

                get_request_json = json.loads(get_request.text)

                # 在函数内为全局变量赋值
                global UserXm
                global UserType
                global UserUnit
                UserXm = get_request_json['UserXm']
                UserType = get_request_json['UserTypeName']
                UserUnit = get_request_json['UserUnitName']
                # 验证通过则跳转到home
                return redirect(url_for('home'))
            else:
                flash(post_request_json['Message'])
    return render_template('login.html', form=form)

@app.route('/home/', methods=['GET','POST'])
def home():
    return render_template('home.html', userunit=UserUnit, userxm=UserXm, usertype=UserType)

@app.route('/introduction/', methods=['GET','POST'])
def introduction():
    return render_template('introduction.html', userunit=UserUnit, userxm=UserXm, usertype=UserType)

@app.route('/websites/', methods=['GET','POST'])
def websites():
    return render_template('websites.html', userunit=UserUnit, userxm=UserXm, usertype=UserType)

@app.route('/offices/', methods=['GET','POST'])
def offices():
    xiaoqu = request.args.get('xiaoqu',type=str)
    if xiaoqu == "大学城校区":
        offices = DxcOffices.query.all()
        result = json.dumps(offices, cls=AlchemyEncoder)
        # print(result)
        return jsonify(result)
    elif xiaoqu == "石牌校区":
        offices = SpOffices.query.all()
        result = json.dumps(offices, cls=AlchemyEncoder)
        return jsonify(result)
    elif xiaoqu == "南海校区":
        offices = NhOffices.query.all()
        result = json.dumps(offices, cls=AlchemyEncoder)
        return jsonify(result)
    return render_template('offices.html', userunit=UserUnit, userxm=UserXm, usertype=UserType)

@app.route('/faq/', methods=['GET','POST'])
def faq():
    cos_sim = []
    noanswer = "哎，脑子被的士搭走了，这个问题回答不了...T_T"
    question = request.args.get('question', type=str)
    if not (question is None):
        if question.strip() != "":
            all_result = Faq.query.all()
            all_result_json = json.dumps(all_result, cls=AlchemyEncoder)
            result = json.loads(all_result_json)
            for item in result:
                vec1, vec2 = get_word_vector(question, item['question'])
                dist = cos_dist(vec1, vec2)
                cos_sim.append(dist)
            # print(cos_sim)
            if max(cos_sim) >= 0.3:
                answer = result[cos_sim.index(max(cos_sim))]['answer']
                answer_json = json.dumps(answer)
                return jsonify(answer_json)
            else:
                noanswer_json = json.dumps(noanswer)
                return jsonify(noanswer_json)
    return render_template('faq.html', userunit=UserUnit, userxm=UserXm, usertype=UserType)

@app.route('/association-dxc/', methods=['GET','POST'])
def association_dxc():
    leixing = request.args.get('leixing', type=str)
    if leixing == "社会实践类":
        asso = DxcAsso.query.filter_by(type="社会实践类").all()
        result = json.dumps(asso, cls=AlchemyEncoder)
        # print(result)
        return jsonify(result)
    elif leixing == "文娱体育类":
        asso = DxcAsso.query.filter_by(type="文娱体育类").all()
        result = json.dumps(asso, cls=AlchemyEncoder)
        return jsonify(result)
    elif leixing == "学术科技类":
        asso = DxcAsso.query.filter_by(type="学术科技类").all()
        result = json.dumps(asso, cls=AlchemyEncoder)
        return jsonify(result)
    elif leixing == "兴趣爱好类":
        asso = DxcAsso.query.filter_by(type="兴趣爱好类").all()
        result = json.dumps(asso, cls=AlchemyEncoder)
        return jsonify(result)
    elif leixing == "院级社联":
        asso = DxcAsso.query.filter_by(type="院级社联").all()
        result = json.dumps(asso, cls=AlchemyEncoder)
        return jsonify(result)
    return render_template('association-dxc.html', userunit=UserUnit, userxm=UserXm, usertype=UserType)

@app.route('/association-sp/', methods=['GET','POST'])
def association_sp():
    leixing = request.args.get('leixing', type=str)
    if leixing == "社会实践类":
        asso = SpAsso.query.filter_by(type="社会实践类").all()
        result = json.dumps(asso, cls=AlchemyEncoder)
        return jsonify(result)
    elif leixing == "文娱体育类":
        asso = SpAsso.query.filter_by(type="文娱体育类").all()
        result = json.dumps(asso, cls=AlchemyEncoder)
        return jsonify(result)
    elif leixing == "学术科技类":
        asso = SpAsso.query.filter_by(type="学术科技类").all()
        result = json.dumps(asso, cls=AlchemyEncoder)
        return jsonify(result)
    elif leixing == "兴趣爱好类":
        asso = SpAsso.query.filter_by(type="兴趣爱好类").all()
        result = json.dumps(asso, cls=AlchemyEncoder)
        return jsonify(result)
    return render_template('association-sp.html', userunit=UserUnit, userxm=UserXm, usertype=UserType)

@app.route('/association-nh/', methods=['GET','POST'])
def association_nh():
    leixing = request.args.get('leixing', type=str)
    if leixing == "社会实践类":
        asso = NhAsso.query.filter_by(type="社会实践类").all()
        result = json.dumps(asso, cls=AlchemyEncoder)
        return jsonify(result)
    elif leixing == "文娱体育类":
        asso = NhAsso.query.filter_by(type="文娱体育类").all()
        result = json.dumps(asso, cls=AlchemyEncoder)
        return jsonify(result)
    elif leixing == "学术科技类":
        asso = NhAsso.query.filter_by(type="学术科技类").all()
        result = json.dumps(asso, cls=AlchemyEncoder)
        return jsonify(result)
    elif leixing == "兴趣爱好类":
        asso = NhAsso.query.filter_by(type="兴趣爱好类").all()
        result = json.dumps(asso, cls=AlchemyEncoder)
        return jsonify(result)
    return render_template('association-nh.html', userunit=UserUnit, userxm=UserXm, usertype=UserType)

if __name__ == '__main__':
    app.run()
