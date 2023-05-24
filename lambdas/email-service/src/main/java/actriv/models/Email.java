package actriv.models;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Email {
    private String type;
    private String subject;
    private EmailParticipants participants;
    private Map<String, Object> body;
    private List<String> attachments;
}
