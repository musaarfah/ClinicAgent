const FLOW_DEFINITIONS = {
  'new-patient': {
    id: 'new-patient',
    label: 'New patient registration',
    shortLabel: 'New patient',
    description: 'I will collect the basics needed to start a new patient intake request.',
    intro:
      'Let’s start a new patient registration. I’ll keep this to the basic scheduling details and leave sensitive medical information out of chat.',
    confirmationIntro:
      'Review the intake details below. Confirm when they look right and I’ll hand them to the assistant.',
    steps: [
      {
        key: 'fullName',
        label: 'Full name',
        prompt: 'What is the patient’s full name?',
        placeholder: 'Enter full name',
      },
      {
        key: 'dateOfBirth',
        label: 'Date of birth',
        prompt: 'What is the patient’s date of birth?',
        placeholder: 'YYYY-MM-DD',
      },
      {
        key: 'contact',
        label: 'Phone or email',
        prompt: 'What is the best phone number or email address to use for scheduling updates?',
        placeholder: 'Phone or email',
      },
      {
        key: 'visitNeed',
        label: 'Visit need',
        prompt: 'What kind of visit is needed?',
        placeholder: 'Annual checkup, follow-up, urgent consult',
      },
      {
        key: 'availability',
        label: 'Preferred timing',
        prompt: 'What day or time window works best for the appointment?',
        placeholder: 'Next week, mornings, after 3 PM',
      },
    ],
  },
  'returning-patient': {
    id: 'returning-patient',
    label: 'Returning patient help',
    shortLabel: 'Returning patient',
    description:
      'Capture the minimum details needed to help an existing patient without exposing records in chat.',
    intro:
      'I can help a returning patient with scheduling, rescheduling, or visit questions. I’ll capture the request and keep verification lightweight for this demo.',
    confirmationIntro:
      'Review the returning patient request below. Confirm when you want me to send it.',
    steps: [
      {
        key: 'fullName',
        label: 'Full name',
        prompt: 'What is the patient’s full name?',
        placeholder: 'Enter full name',
      },
      {
        key: 'dateOfBirth',
        label: 'Date of birth',
        prompt: 'What is the patient’s date of birth?',
        placeholder: 'YYYY-MM-DD',
      },
      {
        key: 'requestType',
        label: 'Request type',
        prompt: 'What does the patient need help with today?',
        placeholder: 'Book follow-up, reschedule, ask about visit prep',
      },
      {
        key: 'timing',
        label: 'Preferred timing',
        prompt: 'What timing or availability should I use for the request?',
        placeholder: 'Friday afternoon, next available',
      },
    ],
  },
  'book-appointment': {
    id: 'book-appointment',
    label: 'Appointment booking',
    shortLabel: 'Book visit',
    description: 'Collect the key scheduling inputs and send a structured booking request.',
    intro:
      'I’ll help you prepare an appointment booking request. I’ll focus on visit type, timing, and contact details so the assistant can respond clearly.',
    confirmationIntro:
      'Review the booking request below. Confirm when you want me to send it.',
    steps: [
      {
        key: 'patientName',
        label: 'Patient name',
        prompt: 'Who is the appointment for?',
        placeholder: 'Enter patient name',
      },
      {
        key: 'visitType',
        label: 'Visit type',
        prompt: 'What kind of appointment would you like to book?',
        placeholder: 'Routine checkup, consultation, follow-up',
      },
      {
        key: 'providerPreference',
        label: 'Provider preference',
        prompt: 'Do you have a preferred doctor or clinic location?',
        placeholder: 'Any provider, Dr. Lee, Downtown clinic',
      },
      {
        key: 'availability',
        label: 'Preferred timing',
        prompt: 'What dates or time windows work best?',
        placeholder: 'This Thursday after 1 PM, next Monday morning',
      },
      {
        key: 'contact',
        label: 'Contact details',
        prompt: 'What contact method should be used for updates?',
        placeholder: 'Phone or email',
      },
    ],
  },
  reschedule: {
    id: 'reschedule',
    label: 'Reschedule appointment',
    shortLabel: 'Reschedule',
    description: 'Gather the current booking context and the new timing request.',
    intro:
      'I can help prepare a reschedule request. I’ll capture the current appointment reference and the new preferred timing.',
    confirmationIntro:
      'Review the reschedule request below. Confirm when it is ready to send.',
    steps: [
      {
        key: 'patientName',
        label: 'Patient name',
        prompt: 'Who needs to reschedule the appointment?',
        placeholder: 'Enter patient name',
      },
      {
        key: 'currentAppointment',
        label: 'Current appointment',
        prompt: 'What is the current appointment date, time, or visit reference?',
        placeholder: 'May 20 at 10 AM with Dr. Patel',
      },
      {
        key: 'newTiming',
        label: 'New preferred timing',
        prompt: 'What would be a better date or time?',
        placeholder: 'Any morning next week',
      },
      {
        key: 'reason',
        label: 'Reason',
        prompt: 'Is there anything the clinic should know about the change?',
        placeholder: 'Travel conflict, need earlier slot',
      },
    ],
  },
  'clinic-info': {
    id: 'clinic-info',
    label: 'Clinic information',
    shortLabel: 'Clinic info',
    description: 'Turn a general clinic question into a clear assistant request.',
    intro:
      'I can help with clinic information such as hours, visit prep, scheduling policy, or appointment steps.',
    confirmationIntro:
      'Review the clinic question below. Confirm when you want me to send it.',
    steps: [
      {
        key: 'topic',
        label: 'Topic',
        prompt: 'What would you like to know about the clinic?',
        placeholder: 'Hours, preparation, cancellation rules',
      },
      {
        key: 'detail',
        label: 'Question detail',
        prompt: 'What is the exact question or situation?',
        placeholder: 'Can I cancel online on the same day?',
      },
    ],
  },
};

const FLOW_ORDER = [
  'new-patient',
  'returning-patient',
  'book-appointment',
  'reschedule',
  'clinic-info',
];

function getFlow(flowId) {
  return FLOW_DEFINITIONS[flowId];
}

function getOrderedFlows() {
  return FLOW_ORDER.map((flowId) => FLOW_DEFINITIONS[flowId]);
}

function getFlowSummary(flowId, answers) {
  const flow = getFlow(flowId);

  return flow.steps
    .filter((step) => answers[step.key])
    .map((step) => ({
      label: step.label,
      value: answers[step.key],
    }));
}

function buildFlowSubmissionMessage(flowId, answers) {
  const flow = getFlow(flowId);
  const summary = getFlowSummary(flowId, answers)
    .map((item) => `- ${item.label}: ${item.value}`)
    .join('\n');

  return [
    `${flow.label}`,
    '',
    'Please handle this request using the details below. Restate the information clearly, note any missing details if relevant, and explain the next scheduling step.',
    '',
    summary,
  ].join('\n');
}

export { buildFlowSubmissionMessage, getFlow, getFlowSummary, getOrderedFlows };
