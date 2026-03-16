import {type FC} from 'react';

export type LanguageCode = 'en' | 'ru';

interface FlagIconProps {
    language: LanguageCode;
    className?: string;
}

export const FlagIcon: FC<FlagIconProps> = ({language}) => {
    const flags = {
        en: (
            <svg width="24" height="16" viewBox="0 0 24 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <g clip-path="url(#clip0_3011_2442)">
                    <mask id="mask0_3011_2442" maskUnits="userSpaceOnUse" x="0" y="0" width="24" height="16">
                        <path
                            d="M21.7143 0H2.28571C1.02335 0 0 0.955126 0 2.13333V13.8667C0 15.0449 1.02335 16 2.28571 16H21.7143C22.9767 16 24 15.0449 24 13.8667V2.13333C24 0.955126 22.9767 0 21.7143 0Z"
                            fill="white"
                        />
                    </mask>
                    <g mask="url(#mask0_3011_2442)">
                        <path
                            d="M21.7143 0H2.28571C1.02335 0 0 0.955126 0 2.13333V13.8667C0 15.0449 1.02335 16 2.28571 16H21.7143C22.9767 16 24 15.0449 24 13.8667V2.13333C24 0.955126 22.9767 0 21.7143 0Z"
                            fill="white"
                        />
                        <path fill-rule="evenodd" clip-rule="evenodd" d="M0 0H10.2857V7.46667H0V0Z" fill="#444379" />
                        <path
                            fill-rule="evenodd"
                            clip-rule="evenodd"
                            d="M1.14258 1.06668V2.13335H2.28544V1.06668H1.14258ZM3.42829 1.06668V2.13335H4.57115V1.06668H3.42829ZM5.71401 1.06668V2.13335H6.85686V1.06668H5.71401ZM7.99972 1.06668V2.13335H9.14258V1.06668H7.99972ZM6.85686 2.13335V3.20001H7.99972V2.13335H6.85686ZM4.57115 2.13335V3.20001H5.71401V2.13335H4.57115ZM2.28544 2.13335V3.20001H3.42829V2.13335H2.28544ZM1.14258 3.20001V4.26668H2.28544V3.20001H1.14258ZM3.42829 3.20001V4.26668H4.57115V3.20001H3.42829ZM5.71401 3.20001V4.26668H6.85686V3.20001H5.71401ZM7.99972 3.20001V4.26668H9.14258V3.20001H7.99972ZM1.14258 5.33335V6.40001H2.28544V5.33335H1.14258ZM3.42829 5.33335V6.40001H4.57115V5.33335H3.42829ZM5.71401 5.33335V6.40001H6.85686V5.33335H5.71401ZM7.99972 5.33335V6.40001H9.14258V5.33335H7.99972ZM6.85686 4.26668V5.33335H7.99972V4.26668H6.85686ZM4.57115 4.26668V5.33335H5.71401V4.26668H4.57115ZM2.28544 4.26668V5.33335H3.42829V4.26668H2.28544Z"
                            fill="#A7B6E7"
                        />
                        <path
                            fill-rule="evenodd"
                            clip-rule="evenodd"
                            d="M10.2857 0V1.06667H24V0H10.2857ZM10.2857 2.13333V3.2H24V2.13333H10.2857ZM10.2857 4.26667V5.33333H24V4.26667H10.2857ZM10.2857 6.4V7.46667H24V6.4H10.2857ZM0 8.53333V9.6H24V8.53333H0ZM0 10.6667V11.7333H24V10.6667H0ZM0 12.8V13.8667H24V12.8H0ZM0 14.9333V16H24V14.9333H0Z"
                            fill="#ED4C49"
                        />
                        <path
                            d="M21.7141 0.533325H2.28557C1.3388 0.533325 0.571289 1.24967 0.571289 2.13333V13.8667C0.571289 14.7503 1.3388 15.4667 2.28557 15.4667H21.7141C22.6609 15.4667 23.4284 14.7503 23.4284 13.8667V2.13333C23.4284 1.24967 22.6609 0.533325 21.7141 0.533325Z"
                            stroke="black"
                            stroke-opacity="0.1"
                            stroke-width="1.14286"
                        />
                    </g>
                </g>
                <defs>
                    <clipPath id="clip0_3011_2442">
                        <rect width="24" height="16" fill="white" />
                    </clipPath>
                </defs>
            </svg>
        ),
        ru: (
            <svg width="24" height="16" viewBox="0 0 24 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <g clip-path="url(#clip0_3011_1028)">
                    <mask id="mask0_3011_1028" maskUnits="userSpaceOnUse" x="0" y="0" width="24" height="16">
                        <path
                            d="M21.7143 0H2.28571C1.02335 0 0 0.955126 0 2.13333V13.8667C0 15.0449 1.02335 16 2.28571 16H21.7143C22.9767 16 24 15.0449 24 13.8667V2.13333C24 0.955126 22.9767 0 21.7143 0Z"
                            fill="white"
                        />
                    </mask>
                    <g mask="url(#mask0_3011_1028)">
                        <path
                            d="M21.7143 0H2.28571C1.02335 0 0 0.955126 0 2.13333V13.8667C0 15.0449 1.02335 16 2.28571 16H21.7143C22.9767 16 24 15.0449 24 13.8667V2.13333C24 0.955126 22.9767 0 21.7143 0Z"
                            fill="#0034A9"
                        />
                        <path fill-rule="evenodd" clip-rule="evenodd" d="M0 10.6667H24V16H0V10.6667Z" fill="#D7280F" />
                        <path fill-rule="evenodd" clip-rule="evenodd" d="M0 0H24V5.33333H0V0Z" fill="white" />
                        <path
                            d="M21.7141 0.533325H2.28557C1.3388 0.533325 0.571289 1.24967 0.571289 2.13333V13.8667C0.571289 14.7503 1.3388 15.4667 2.28557 15.4667H21.7141C22.6609 15.4667 23.4284 14.7503 23.4284 13.8667V2.13333C23.4284 1.24967 22.6609 0.533325 21.7141 0.533325Z"
                            stroke="black"
                            stroke-opacity="0.1"
                            stroke-width="1.14286"
                        />
                    </g>
                </g>
                <defs>
                    <clipPath id="clip0_3011_1028">
                        <rect width="24" height="16" fill="white" />
                    </clipPath>
                </defs>
            </svg>
        ),
    };

    return flags[language] || flags.en;
};
