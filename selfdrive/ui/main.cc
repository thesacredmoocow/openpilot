#include <sys/resource.h>
#include <iostream>

#include <QApplication>
#include <QWidget>
#include <QWindow>
#include <QMainWindow>
#include <QTranslator>
#include <QDebug>
#include <QProcess>

#include "system/hardware/hw.h"
#include "selfdrive/ui/qt/qt_window.h"
#include "selfdrive/ui/qt/util.h"
#include "selfdrive/ui/qt/window.h"
#include "selfdrive/ui/defines.h"

int main(int argc, char *argv[]) {
  setpriority(PRIO_PROCESS, 0, -20);

  qInstallMessageHandler(swagLogMessageHandler);
  initApp(argc, argv);

  QTranslator translator;
  QString translation_file = QString::fromStdString(Params().get("LanguageSetting"));
  if (!translator.load(translation_file, "translations") && translation_file.length()) {
    qCritical() << "Failed to load translation file:" << translation_file;
  }

  QApplication a(argc, argv);
  a.installTranslator(&translator);

  MainWindow w;

  QRect screen2location = a.screens().last()->geometry();
  
  w.move(screen2location.x(), screen2location.y());
  w.resize(screen2location.width(), screen2location.height());
  w.showFullScreen();
  a.installEventFilter(&w);

  #ifdef SHOWINFOTAINMENT
    QProcess *process = new QProcess(&w);
    process->start("/home/thesacredmoocow/openpilot/selfdrive/ui/dash/bin/dash");
  #endif
  
  return a.exec();
}
