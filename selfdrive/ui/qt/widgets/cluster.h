#pragma once

#include <QWidget>
#include <QTimer>
#include <QTime>
#include <QPainter>

class Cluster : public QWidget
{
    Q_OBJECT

public:
    Cluster(QWidget *parent = nullptr);

protected:
    //void paintEvent(QPaintEvent *event) override;
};