#include <QCollator>
#include <QCoreApplication>
#include <QDnsLookup>
#include <QFile>
#include <QLocale>
#include <QNetworkAccessManager>
#include <QNetworkDatagram>
#include <QNetworkProxy>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QRegularExpression>
#include <QResource>
#include <QSignalSpy>
#include <QTcpServer>
#include <QTcpSocket>
#include <QUdpSocket>
#include <QVariant>
#include <iostream>
#include <memory>
#include <stdexcept>

namespace {
void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

void dnsLookup() {
    // Use a local DNS responder. Windows DnsQueryEx requires the standard port.
    QUdpSocket server;
#ifdef Q_OS_WIN
    constexpr quint16 port = 53;
#else
    constexpr quint16 port = 0;
#endif
    require(server.bind(QHostAddress(QHostAddress::LocalHost), port, QUdpSocket::DontShareAddress),
            "Local DNS server bind (Windows requires free UDP port 53 on loopback)");
    QObject::connect(&server, &QUdpSocket::readyRead, [&] {
        while (server.hasPendingDatagrams()) {
            const auto datagram = server.receiveDatagram();
            const auto query = datagram.data();
            if (query.size() < 17) continue;
            qsizetype end = 12;
            while (end < query.size() && query[end] != '\0') {
                const auto length = static_cast<unsigned char>(query[end]);
                if (length > 63) return;
                end += 1 + length;
            }
            end += 5; // terminating zero, QTYPE and QCLASS
            if (end > query.size()) continue;
            auto response = query.left(2) + QByteArray::fromHex("81800001000100000000");
            response += query.mid(12, end - 12);
            // One TXT answer, TTL 60, containing the ten-byte string "sdk-dns-ok".
            response += QByteArray::fromHex("c00c001000010000003c000b0a");
            response += "sdk-dns-ok";
            server.writeDatagram(response, datagram.senderAddress(), datagram.senderPort());
        }
    });
    QDnsLookup lookup(QDnsLookup::TXT,
                      QStringLiteral("sdk-%1.example.test").arg(QCoreApplication::applicationPid()));
    lookup.setNameserver(QHostAddress::LocalHost, server.localPort());
    QSignalSpy finished(&lookup, &QDnsLookup::finished);
    require(finished.isValid(), "Qt Test QSignalSpy");
    lookup.lookup();
    require(!finished.isEmpty() || finished.wait(10000), "DNS lookup timeout");
    if (lookup.error() != QDnsLookup::NoError)
        throw std::runtime_error("DNS lookup: " + lookup.errorString().toStdString());
    const auto records = lookup.textRecords();
    require(records.size() == 1 && records.front().values() == QList<QByteArray>{"sdk-dns-ok"},
            "DNS TXT result");
}

void brotliHttp() {
    QTcpServer server;
    require(server.listen(QHostAddress::LocalHost, 0), "HTTP server bind");
    bool advertised = false;
    QObject::connect(&server, &QTcpServer::newConnection, [&] {
        while (auto* socket = server.nextPendingConnection()) {
            QObject::connect(socket, &QTcpSocket::disconnected, socket, &QObject::deleteLater);
            QObject::connect(socket, &QTcpSocket::readyRead, socket, [&, socket] {
                const auto request = socket->property("request").toByteArray() + socket->readAll();
                socket->setProperty("request", request);
                if (!request.contains("\r\n\r\n")) return;
                for (const auto& line : request.toLower().split('\n'))
                    if (line.startsWith("accept-encoding:")) advertised = line.contains("br");
                // Brotli 1.2.0: eight repetitions of the expected plain-text line below.
                const auto body = QByteArray::fromHex(
                    "1b0f0100049c63dd9296b2a159e2e17038b622c90cb498b62ecd1329feeb0e1aac2aea468902");
                socket->write("HTTP/1.1 200 OK\r\nContent-Encoding: br\r\nContent-Length: "
                              + QByteArray::number(body.size())
                              + "\r\nConnection: close\r\n\r\n" + body);
                socket->disconnectFromHost();
            });
        }
    });
    QNetworkAccessManager network;
    network.setProxy(QNetworkProxy::NoProxy);
    std::unique_ptr<QNetworkReply> reply(network.get(QNetworkRequest(
        QUrl(QStringLiteral("http://127.0.0.1:%1/").arg(server.serverPort())))));
    QSignalSpy finished(reply.get(), &QNetworkReply::finished);
    require(!finished.isEmpty() || finished.wait(10000), "Brotli HTTP timeout");
    require(reply->error() == QNetworkReply::NoError, "Brotli HTTP response");
    require(advertised, "Qt Network did not advertise Brotli support");
    require(reply->readAll() == QByteArray("Qt Brotli local HTTP verification\n").repeated(8),
            "Qt Network Brotli decompression");
}
}

int main(int argc, char** argv) {
    QCoreApplication app(argc, argv);
    try {
        QCollator collator(QLocale(QLocale::English, QLocale::UnitedStates));
        collator.setNumericMode(true);
        require(collator.compare(QStringLiteral("file2"), QStringLiteral("file10")) < 0,
                "Unicode numeric collation");
        QRegularExpression regex(QStringLiteral("^\\p{Han}+$"));
        require(regex.isValid() && regex.match(QString::fromUtf8("中文测试")).hasMatch(),
                "PCRE2 Unicode matching");
        const QResource resource(QStringLiteral(":/sdk/qt-zstd.txt"));
        require(resource.isValid() && resource.compressionAlgorithm() == QResource::ZstdCompression,
                "rcc zstd resource compression");
        QFile file(QStringLiteral(":/sdk/qt-zstd.txt"));
        require(file.open(QIODevice::ReadOnly)
                    && file.readAll() == QByteArray("Qt zstd resource verification\n").repeated(64),
                "Qt zstd resource decompression");
        dnsLookup();
        brotliHttp();
        std::cout << "Qt features: Unicode collation, PCRE2, zstd resources, DNS TXT, "
                     "Brotli HTTP and Qt Test passed\n";
    } catch (const std::exception& error) {
        std::cerr << "Qt feature check failed: " << error.what() << '\n';
        return 1;
    }
}
