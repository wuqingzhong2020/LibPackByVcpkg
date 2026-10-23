#include <QApplication>
#include <QSvgRenderer>
#include <QSerialPortInfo>
#include <QModbusDataUnit>
#include <DockManager.h>
#include <DockWidget.h>
#include <QLabel>
#include <QBuffer>
#include <QColor>
#include <QImage>
#include <QImageReader>
#include <QSqlDatabase>
#include <QSqlQuery>
#include <QSslSocket>
#include <QVariant>
#include <QtConcurrent/QtConcurrentRun>
#include <stdexcept>
int main(int argc,char**argv) {
    QApplication app(argc,argv); ads::CDockManager manager;
    auto* dock=new ads::CDockWidget("SDK"); dock->setWidget(new QLabel("C++20"));
    manager.addDockWidget(ads::TopDockWidgetArea,dock);
    auto state=manager.saveState(); if(!manager.restoreState(state)) throw std::runtime_error("ADS state");
    QSvgRenderer svg(QByteArray("<svg xmlns='http://www.w3.org/2000/svg' width='10' height='10'><rect width='10' height='10'/></svg>"));
    if(!svg.isValid()) throw std::runtime_error("SVG");
    QModbusDataUnit unit(QModbusDataUnit::HoldingRegisters,0,2); unit.setValue(0,42);
    if(unit.value(0)!=42) return 1;
    auto db=QSqlDatabase::addDatabase("QSQLITE"); db.setDatabaseName(":memory:");
    if(!db.open()) throw std::runtime_error("Qt SQLite plugin");
    QSqlQuery query(db);
    if(!query.exec("select 6*7") || !query.next() || query.value(0).toInt()!=42)
        throw std::runtime_error("Qt SQL query");
    if(!QSslSocket::availableBackends().contains("openssl") ||
       !QSslSocket::setActiveBackend("openssl") || !QSslSocket::supportsSsl())
        throw std::runtime_error("Qt OpenSSL TLS backend");
    if(QtConcurrent::run([] { return 42; }).result()!=42) return 2;
    const auto formats=QImageReader::supportedImageFormats();
    if(!formats.contains("tiff") || !formats.contains("webp"))
        throw std::runtime_error("Qt image format plugins");
    QImage image(8,8,QImage::Format_RGB32); image.fill(Qt::red);
    QByteArray bytes; QBuffer buffer(&bytes); buffer.open(QIODevice::WriteOnly);
    if(!image.save(&buffer,"TIFF") || QImage::fromData(bytes,"TIFF").pixelColor(0,0)!=QColor(Qt::red))
        throw std::runtime_error("Qt TIFF round trip");
    (void)QSerialPortInfo::availablePorts(); manager.show(); app.processEvents();
}
