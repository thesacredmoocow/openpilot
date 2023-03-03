#pragma once

#include <QWidget>
#include <QTimer>
#include <QTime>
#include <QPainter>

class RightCluster : public QWidget
{
    Q_OBJECT

public:
    RightCluster(QWidget *parent = nullptr);

protected:

private slots:
    //void updateState(const UIState &s);
};