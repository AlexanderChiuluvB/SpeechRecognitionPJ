import flask
from flask import *
from training import *
from models.VGG import *

if __name__ == "__main__":

    app = flask.Flask(__name__)
    app.debug = True

    model = vgg13_bn()
    optimizer = torch.optim.Adam(model.parameters(), lr=5e-5)
    """
    best2.pth
    VGG11 MEL_SPECTROGRAM 128 FILTERS
    
    best_model_melspec.pth 效果很好啊！！！
    
    """
    checkpointer = torch.load('best_model_melspec.pth',map_location='cpu')
    model.load_state_dict(checkpointer['state_dict'])

    @app.route('/', methods=['POST', 'GET'])
    def home():
        print("open home")
        return send_from_directory('.','index.html')


    @app.route('/static/upload.php', methods=['POST', 'GET'])
    def upload():
        print("running")
        if request.method == 'POST':
            f = request.files['audio_data']
            save_to = "upload/{}".format(f.filename)
            f.save(save_to)
            #index = infer(model,save_to)
            return redirect(url_for('upload'))
        return render_template('index.html')


    @app.route('/save-record', methods=['POST','GET'])
    def save_record():
        print("save_record")
        file = flask.request.files['file']
        app.logger.debug(file.filename)
        label = ["数字","语音","语言","识别","中国","总工",
                           "北京"
                           ,"背景"
                           ,"上海"
                           ,"商行"
                           ,"复旦"
                           ,"饭店"
                           ,"Speech"
                           ,"Speaker",
                           "Signal","Process","Print","Open","Close",
                           "Project"]

        os.makedirs("upload", exist_ok=True)
        save_to = "upload/{}".format(file.filename)
        file.save(save_to)
        print(label[infer(model, save_to)])
        return label[infer(model, save_to)]



    app.run(host="localhost", port=8999)
