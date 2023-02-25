# AssemblyAI Batch Transcribe Tool
Chunk audio files into smaller clips to transcribe them faster with AssemblyAI.

Transcription time is usually ~20% of the original audio file length. One way to speed up this turnaround time is to chunk the file into shorter clips and send them to AssemblyAI to be transcribed concurrently. AssemblyAI allows 32 concurrent jobs by default which can be increased based on customer requirements. Once the jobs are complete, the individual transcripts for each clip can be joined back together and sorted by timestamps to match the original audio clip.

### Steps to run this tool

1. Install libraries in requirements.txt file: `pip3 install -r requirements.txt`
2. Add AssemblyAI API key as an env variable: `export ASSEMBLYAI_API_TOKEN={YOUR_KEY}`
3. Run `python3 clip-chunker.py <path_to_input_file> <clip_length_in_seconds (optional, default=120 seconds)>`

### How it works

![system design](https://github.com/neil-assembly/batch-transcribe-tool/blob/master/clip%20chunker%20system%20design.png)




