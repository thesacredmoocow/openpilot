#include "selfdrive/ui/qt/widgets/right_cluster.h"

RightCluster::RightCluster(QWidget *parent)
    : QWidget(parent)
{
    setFixedWidth(560);
}
/*
void HomeWindow::updateState(const UIState &s) {
  const SubMaster &sm = *(s.sm);

  // switch to the generic robot UI
  if (onroad->isVisible() && !body->isEnabled() && sm["carParams"].getCarParams().getNotCar()) {
    body->setEnabled(true);
    slayout->setCurrentWidget(body);
  }
}*/