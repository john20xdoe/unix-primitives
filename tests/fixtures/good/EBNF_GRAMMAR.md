# Turn Response Grammar
Turn output conforms to a formal grammar specified in RFC 5234 ABNF notation.
Production rules declare strict XOR mutual exclusion between response modes.
The grammar specifies the following lexical structure:
- turn_response consists of a status header followed by mutually exclusive branches.
- Valid branches are either a tool_action invocation or a pause_gate descriptor.
- Emitting both tool actions and human questions in a single turn is forbidden.
Turn negotiation follows Flores speech act transitions (?assert then ?promise).
Syntactic parsers reject malformed frames before reaching semantic handlers.
Grammar decoders enforce schema compliance at generation time.