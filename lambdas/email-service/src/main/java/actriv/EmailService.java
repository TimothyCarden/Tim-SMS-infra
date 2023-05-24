package actriv;

import actriv.models.Email;
import actriv.models.EmailParticipants;
import actriv.models.SQSRecord;
import com.amazonaws.regions.Regions;
import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.SQSEvent;
import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.AmazonS3ClientBuilder;
import com.amazonaws.services.s3.model.GeneratePresignedUrlRequest;
import com.amazonaws.services.s3.model.GetObjectRequest;
import com.amazonaws.services.s3.model.S3Object;
import com.amazonaws.services.simpleemail.AmazonSimpleEmailService;
import com.amazonaws.services.simpleemail.AmazonSimpleEmailServiceClientBuilder;
import com.amazonaws.services.simpleemail.model.RawMessage;
import com.amazonaws.services.simpleemail.model.SendRawEmailRequest;
import com.fasterxml.jackson.databind.ObjectMapper;
import freemarker.cache.URLTemplateLoader;
import freemarker.template.Configuration;
import freemarker.template.Template;
import freemarker.template.TemplateException;

import javax.activation.DataHandler;
import javax.mail.Message;
import javax.mail.MessagingException;
import javax.mail.Session;
import javax.mail.internet.InternetAddress;
import javax.mail.internet.MimeBodyPart;
import javax.mail.internet.MimeMessage;
import javax.mail.internet.MimeMultipart;
import javax.mail.util.ByteArrayDataSource;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.net.URL;
import java.nio.ByteBuffer;
import java.util.List;
import java.util.Properties;

public class EmailService implements RequestHandler<SQSEvent, Void> {

    private static final String EMAIL_TEMPLATE_BUCKET_NAME = "actriv-dev-email-templates-storage";
    private static final String EMAIL_ATTACHMENTS_BUCKET_NAME = "actriv-dev-email-attachements-storage";
    private static final String EMAIL_TEMPLATE_EXTENSION = ".ftlh";

    public Void handleRequest(final SQSEvent input, final Context context) {
        context.getLogger().log("SQSEvent: " + input);
        List<SQSEvent.SQSMessage> records = input.getRecords();
        AmazonSimpleEmailService sesClient = AmazonSimpleEmailServiceClientBuilder.standard().withRegion(Regions.US_WEST_2).build();
        AmazonS3 s3Client = AmazonS3ClientBuilder.standard().withRegion(Regions.US_WEST_2).build();
        Session session = Session.getDefaultInstance(new Properties());
        Configuration configuration = new Configuration(Configuration.VERSION_2_3_28);

        records.forEach(record -> {
            ObjectMapper mapper = new ObjectMapper();
            try {
                SQSRecord sqsRecord = mapper.readValue(record.getBody(), SQSRecord.class);
                Email email = sqsRecord.getEmail();
                String s3ObjectKey = email.getType() + EMAIL_TEMPLATE_EXTENSION;

                Template template = getTemplate(s3Client, configuration, s3ObjectKey);
                RawMessage rawMessage = getRawMessage(session, email, template, s3Client);

                sesClient.sendRawEmail(new SendRawEmailRequest().withRawMessage(rawMessage));
            } catch (Exception e) {
                context.getLogger().log("Error sending email: " + e.getMessage());
                throw new RuntimeException(e);
            }
        });

        return null;
    }

    private static Template getTemplate(AmazonS3 s3Client, Configuration configuration, String s3ObjectKey) throws IOException {
        URLTemplateLoader urlTemplateLoader = getUrlTemplateLoader(s3Client, s3ObjectKey);
        configuration.setTemplateLoader(urlTemplateLoader);
        return configuration.getTemplate(s3ObjectKey);
    }

    private static URLTemplateLoader getUrlTemplateLoader(AmazonS3 s3Client, String s3ObjectKey) {
        return new URLTemplateLoader() {
            @Override
            protected URL getURL(String s) {
                return s3Client.generatePresignedUrl(new GeneratePresignedUrlRequest(EMAIL_TEMPLATE_BUCKET_NAME, s3ObjectKey));
            }
        };
    }

    private static RawMessage getRawMessage(Session session, Email sqsRecordEmail, Template template, AmazonS3 s3Client) throws MessagingException, IOException, TemplateException {
        MimeMessage message = new MimeMessage(session);

        setEmailDetails(sqsRecordEmail, message);
        MimeMultipart msg_body = new MimeMultipart("alternative");
        MimeBodyPart wrap = new MimeBodyPart();
        MimeBodyPart htmlPart = getHtmlPart(sqsRecordEmail, template);
        msg_body.addBodyPart(htmlPart);
        wrap.setContent(msg_body);
        MimeMultipart msg = new MimeMultipart("mixed");
        message.setContent(msg);
        msg.addBodyPart(wrap);

        setAttachments(sqsRecordEmail, s3Client, msg);

        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        message.writeTo(outputStream);
        return new RawMessage(ByteBuffer.wrap(outputStream.toByteArray()));
    }

    private static void setAttachments(Email sqsRecordEmail, AmazonS3 s3Client, MimeMultipart msg) throws IOException, MessagingException {
        List<String> attachments = sqsRecordEmail.getAttachments();
        if (!attachments.isEmpty()) {
            for (String attachment : attachments) {
                S3Object object = s3Client.getObject(new GetObjectRequest(EMAIL_ATTACHMENTS_BUCKET_NAME, attachment));
                byte[] bytes = object.getObjectContent().readAllBytes();
                ByteArrayDataSource dataSource = new ByteArrayDataSource(bytes, object.getObjectMetadata().getContentType());
                MimeBodyPart att = new MimeBodyPart();
                att.setDataHandler(new DataHandler(dataSource));
                att.setFileName(dataSource.getName());
                msg.addBodyPart(att);
            }
        }
    }

    private static MimeBodyPart getHtmlPart(Email sqsRecordEmail, Template template) throws MessagingException, IOException {
        MimeBodyPart htmlPart = new MimeBodyPart();
        ByteArrayOutputStream htmlBodyOutputStream = processHtmlFromTemplate(sqsRecordEmail, template);
        htmlPart.setContent(htmlBodyOutputStream.toString(),"text/html; charset=UTF-8");
        htmlBodyOutputStream.flush();
        return htmlPart;
    }

    private static void setEmailDetails(Email sqsRecordEmail, MimeMessage message) throws MessagingException {
        EmailParticipants participants = sqsRecordEmail.getParticipants();
        message.setSubject(sqsRecordEmail.getSubject(), "UTF-8");
        message.setFrom(new InternetAddress(participants.getFrom()));
        message.setRecipients(Message.RecipientType.TO, InternetAddress.parse(participants.getTo()));
        if (participants.getCc() != null) {
            message.setRecipients(Message.RecipientType.CC, InternetAddress.parse(participants.getCc()));
        }
    }

    private static ByteArrayOutputStream processHtmlFromTemplate(Email sqsRecordEmail, Template template) {
        try (ByteArrayOutputStream outputStream = new ByteArrayOutputStream();) {
            OutputStreamWriter outputStreamWriter = new OutputStreamWriter(outputStream);

            template.process(sqsRecordEmail.getBody(), outputStreamWriter);
            return outputStream;
        } catch (IOException | TemplateException ex) {
            throw new RuntimeException("Error processing template", ex);
        }
    }

}
