<?php

use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Route;

Route::prefix('v1')->group(function (): void {
    Route::get('/health', static fn (): JsonResponse => response()->json([
        'service' => 'research-os-laravel-platform',
        'status' => 'ok',
        'contract_version' => '1.0.0',
    ]));

    Route::get('/ready', static fn (): JsonResponse => response()->json([
        'service' => 'research-os-laravel-platform',
        'status' => 'ready',
        'contract_version' => '1.0.0',
    ]));
});
