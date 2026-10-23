#include <ILexer.h>
#include <Lexilla.h>
int main() {
    auto* lexer=CreateLexer("cpp"); if(!lexer) return 1;
    const bool ok=lexer->NamedStyles()>0; lexer->Release(); return ok?0:2;
}
