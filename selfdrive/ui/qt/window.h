#pragma once

#include <QStackedLayout>
#include <QHBoxLayout>
#include <QWidget>

#include "selfdrive/ui/qt/home.h"
#include "selfdrive/ui/qt/offroad/onboarding.h"
#include "selfdrive/ui/qt/offroad/settings.h"
#include "selfdrive/ui/qt/widgets/cluster.h"
#include "selfdrive/ui/qt/widgets/right_cluster.h"

class MainWindow : public QWidget {
  Q_OBJECT

public:
  explicit MainWindow(QWidget *parent = 0);

private:
  bool eventFilter(QObject *obj, QEvent *event) override;
  void openSettings(int index = 0, const QString &param = "");
  void closeSettings();

  Device device;

  QStackedLayout *main_layout;
  QHBoxLayout *cluster_layout;
  HomeWindow *homeWindow;
  SettingsWindow *settingsWindow;
  OnboardingWindow *onboardingWindow;
  Cluster *clusterWidget;
  RightCluster *rightClusterWidget;
};
