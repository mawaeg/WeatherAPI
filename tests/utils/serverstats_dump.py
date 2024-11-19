serverstats_live_dump: dict = {
    "data": {
        "cpu-usage": 2.43902,
        "uptime": {"seconds": 1159709, "date": "2024-05-05T08:54:15.984528Z", "human": "1 Woche"},
        "load-average": ["0.04", "0.03", "0.05"],
        "memory-usage": {
            "mem-total": 2097,
            "mem-free": 110.8,
            "mem-available": 603,
            "swap-total": 0,
            "swap-free": 0,
            "mem-used": 1494,
        },
        "disk-space": {"size": 24.48, "used": 4.36, "available": 19.05, "use": 19},
    },
}

serverstats_history_dump: dict = {
    "data": {
        "chart": {
            "full_cpu_usage": {
                "labels": [
                    "18.02.2024 21:16",
                    "18.02.2024 22:58",
                    "19.02.2024 01:57",
                    "19.02.2024 04:17",
                    "19.02.2024 07:31",
                ],
                "data": [0, 4.82, 2.38, 0, 0],
            },
            "load_per_core": {
                "labels": [
                    "18.02.2024 21:16",
                    "18.02.2024 22:58",
                    "19.02.2024 01:57",
                    "19.02.2024 04:17",
                    "19.02.2024 07:31",
                ],
                "data": [0.01, 0.02, 0.02, 0.02, 0.02],
            },
            "memory_usage": {
                "labels": [
                    "18.02.2024 21:16",
                    "18.02.2024 22:58",
                    "19.02.2024 01:57",
                    "19.02.2024 04:17",
                    "19.02.2024 07:31",
                ],
                "data": [12, 12, 12, 12, 12],
            },
            "memory_used": {
                "labels": [
                    "18.02.2024 21:16",
                    "18.02.2024 22:58",
                    "19.02.2024 01:57",
                    "19.02.2024 04:17",
                    "19.02.2024 07:31",
                ],
                "data": [242, 242, 242.5, 242, 242],
            },
            "disk_usage": {
                "labels": [
                    "18.02.2024 21:16",
                    "18.02.2024 22:58",
                    "19.02.2024 01:57",
                    "19.02.2024 04:17",
                    "19.02.2024 07:31",
                ],
                "data": [9, 9, 9, 9, 9],
            },
            "disk_used": {
                "labels": [
                    "18.02.2024 21:16",
                    "18.02.2024 22:58",
                    "19.02.2024 01:57",
                    "19.02.2024 04:17",
                    "19.02.2024 07:31",
                ],
                "data": [2.29, 2.29, 2.32, 2.32, 2.32],
            },
            "updates_available": {
                "labels": [
                    "18.02.2024 21:16",
                    "18.02.2024 22:58",
                    "19.02.2024 01:57",
                    "19.02.2024 04:17",
                    "19.02.2024 07:31",
                ],
                "data": [0, 0, 0, 0, 5],
            },
            "uptime": {
                "labels": [
                    "18.02.2024 21:16",
                    "18.02.2024 22:58",
                    "19.02.2024 01:57",
                    "19.02.2024 04:17",
                    "19.02.2024 07:31",
                ],
                "data": [936, 937, 940, 943, 946],
            },
            "traffic_total": {
                "labels": [
                    "18.02.2024 21:16",
                    "18.02.2024 22:58",
                    "19.02.2024 01:57",
                    "19.02.2024 04:17",
                    "19.02.2024 07:31",
                ],
                "data": [1.1, 1.2, 1.2, 1.2, 1.25],
            },
        }
    }
}

serverstats_history_expected_result: list[dict] = [
    {
        "date": "18.02.2024 21:16",
        "full_cpu_usage": 0.0,
        "load_per_core": 0.01,
        "memory_usage": 12.0,
        "memory_used": 242.0,
        "disk_usage": 9.0,
        "disk_used": 2.29,
        "updates_available": 0.0,
        "uptime": 936,
        "traffic_total": 1.1,
    },
    {
        "date": "18.02.2024 22:58",
        "full_cpu_usage": 4.82,
        "load_per_core": 0.02,
        "memory_usage": 12.0,
        "memory_used": 242.0,
        "disk_usage": 9.0,
        "disk_used": 2.29,
        "updates_available": 0.0,
        "uptime": 937,
        "traffic_total": 1.2,
    },
    {
        "date": "19.02.2024 01:57",
        "full_cpu_usage": 2.38,
        "load_per_core": 0.02,
        "memory_usage": 12.0,
        "memory_used": 242.5,
        "disk_usage": 9.0,
        "disk_used": 2.32,
        "updates_available": 0.0,
        "uptime": 940,
        "traffic_total": 1.2,
    },
    {
        "date": "19.02.2024 04:17",
        "full_cpu_usage": 0.0,
        "load_per_core": 0.02,
        "memory_usage": 12.0,
        "memory_used": 242.0,
        "disk_usage": 9.0,
        "disk_used": 2.32,
        "updates_available": 0.0,
        "uptime": 943,
        "traffic_total": 1.2,
    },
    {
        "date": "19.02.2024 07:31",
        "full_cpu_usage": 0.0,
        "load_per_core": 0.02,
        "memory_usage": 12.0,
        "memory_used": 242.0,
        "disk_usage": 9.0,
        "disk_used": 2.32,
        "updates_available": 5.0,
        "uptime": 946,
        "traffic_total": 1.25,
    },
]
