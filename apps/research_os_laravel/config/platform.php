<?php

return [
    'canonical' => [
        'base_url' => env('RESEARCH_OS_PLATFORM_URL', ''),
        'timeout' => (float) env('RESEARCH_OS_PLATFORM_TIMEOUT', 10),
        'connect_timeout' => (float) env('RESEARCH_OS_PLATFORM_CONNECT_TIMEOUT', 3),
    ],
    'endpoints' => [
        'identity' => '/api/v1/platform/identity/resolve',
        'authorization' => '/api/v1/platform/authorization/decide',
        'workflow' => '/api/v1/platform/workflow/dispatch',
        'messaging' => '/api/v1/platform/messaging/publish',
        'evidence' => '/api/v1/platform/evidence',
        'audit' => '/api/v1/platform/audit',
    ],
];
