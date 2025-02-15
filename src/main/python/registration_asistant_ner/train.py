def train():
    train_data, test_data, eval_data = load_data()
    model = load_model()
    model.train(train_data, test_data, eval_data)
    model.save()
    

if __name__ == '__main__':
    train()