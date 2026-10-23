#include <QApplication>
#include <QtNodes/DataFlowGraphModel>
#include <QtNodes/NodeDelegateModelRegistry>
#include <SARibbonMainWindow.h>
#include <SARibbonBar.h>
#include <ScintillaEditBase.h>
#include <Scintillua.h>
#include <memory>
#include <stdexcept>
int main(int argc,char** argv) {
    QApplication app(argc,argv);
    auto registry=std::make_shared<QtNodes::NodeDelegateModelRegistry>();
    QtNodes::DataFlowGraphModel model(registry);
    if(!model.allNodeIds().empty()) return 1;
    SARibbonMainWindow ribbon; ribbon.ribbonBar()->addCategoryPage("SDK");
    ScintillaEditBase editor;
    SetLibraryProperty("scintillua.lexers",SDK_LEXERS);
    auto* lexer=CreateLexer("lua");
    if(!lexer) throw std::runtime_error(GetCreateLexerError());
    editor.send(SCI_SETILEXER,0,reinterpret_cast<sptr_t>(lexer));
    editor.sends(SCI_SETTEXT,0,"local answer = 42 -- comment\n");
    editor.send(SCI_COLOURISE,0,-1);
    if(editor.send(SCI_GETLENGTH)==0 || editor.send(SCI_GETSTYLEAT,0)==0) return 2;
    ribbon.show(); editor.show(); app.processEvents();
}
