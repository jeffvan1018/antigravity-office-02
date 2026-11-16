extends ColorRect

@onready var output_log: RichTextLabel = $MarginContainer/VBoxContainer/OutputLog
@onready var command_input: LineEdit = $MarginContainer/VBoxContainer/InputRow/CommandInput


func _ready() -> void:
	command_input.text_submitted.connect(_on_command_submitted)
	command_input.grab_focus()
	_append_line("Welcome to Antigravity Office. Type 'help' for commands.")


func _on_command_submitted(raw_text: String) -> void:
	var cmd := raw_text.strip_edges()
	command_input.clear()
	if cmd.is_empty():
		return

	_append_line("> " + cmd)
	_handle_command(cmd.to_lower())
	command_input.grab_focus()


func _handle_command(cmd: String) -> void:
	match cmd:
		"help":
			_append_line("Available commands: look, help, clear")
		"look":
			_append_line("You are in the Google Antigravity office. There's a developer desk and chair nearby.")
		"clear":
			output_log.clear()
		_:
			_append_line("I don't understand '%s'." % cmd)


func _append_line(text: String) -> void:
	output_log.append_text(text + "\n")
